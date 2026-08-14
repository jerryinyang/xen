"""Quantify EXP-100's ATR-undefined initial-observation excursion defect.

Analyst-owned: reads only the frozen raw emissions.  The completed observation
mark is an exact aggregate of its emitted source-minute window, so its side-aware
high/low identifies the correct initial-observation maximum even though the
individual source minutes are not emitted.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl

REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "data/nautilus_runs/EXP-100/full"
OUT = REPO / "python/experiments/EXP-100/results/analysis/atr_undefined_prevalence.json"
TOLERANCE = 1e-12
QUANTILES = (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0)
LAYERS = ("instrument", "timeframe", "config", "method", "confirm_ref")
RAID_COLUMNS = [
    "raid_id",
    "side",
    "level_price",
    "sweep_ts_ns",
    "first_excursion_ts_ns",
    "max_price",
    "max_excursion",
    "max_excursion_bps",
    "max_excursion_atr",
    "raid_atr",
    "profile_generation",
    "profile_undefined_reason",
    "confirmation_ts_ns",
    "primary_attribution",
    "status",
    "swing_atr",
    "strong_move",
]


def parse_cell(cell_id: str) -> dict[str, str]:
    parts = cell_id.split("-")
    return {
        "cell_id": cell_id,
        "instrument": parts[1].upper(),
        "timeframe": parts[2],
        "method": parts[3],
        "confirm_ref": parts[4],
        "config": "_".join(parts[5:]).upper(),
    }


def reconstruct_exposure(
    raids: pl.DataFrame,
    profiles: pl.DataFrame,
    marks: pl.DataFrame,
) -> pl.DataFrame:
    """Return ATR-undefined raids with the emitted observation extreme reconstructed."""
    atr_raids = raids.filter(pl.col("profile_undefined_reason") == "ATR_UNDEFINED")
    atr_profiles = profiles.filter(
        (pl.col("profile_status") == "UNDEFINED")
        & (pl.col("undefined_reason") == "ATR_UNDEFINED")
    ).select("raid_id")
    invalid_path = atr_raids.filter(
        pl.col("profile_generation").is_not_null() | pl.col("raid_atr").is_not_null()
    ).height
    if invalid_path:
        raise ValueError(f"{invalid_path} ATR_UNDEFINED raids did not take the no-profile path")
    if set(atr_raids["raid_id"]) != set(atr_profiles["raid_id"]):
        raise ValueError("raid/profile ATR_UNDEFINED populations disagree")

    result = atr_raids.join(
        marks.select("ts_event_ns", "RealHigh", "RealLow"),
        left_on="sweep_ts_ns",
        right_on="ts_event_ns",
        how="left",
        validate="m:1",
    )
    if result["RealHigh"].null_count() or result["RealLow"].null_count():
        raise ValueError("ATR_UNDEFINED raid has no completed observation mark")

    result = result.with_columns(
        pl.when(pl.col("side") == "HIGH")
        .then(pl.col("RealHigh"))
        .otherwise(pl.col("RealLow"))
        .alias("reconstructed_initial_max_price"),
        pl.when(pl.col("side") == "HIGH")
        .then(pl.col("max_price") - pl.col("level_price"))
        .otherwise(pl.col("level_price") - pl.col("max_price"))
        .alias("excursion_from_emitted_max_price"),
    ).with_columns(
        pl.when(pl.col("side") == "HIGH")
        .then(pl.col("reconstructed_initial_max_price") - pl.col("level_price"))
        .otherwise(pl.col("level_price") - pl.col("reconstructed_initial_max_price"))
        .alias("reconstructed_initial_max_excursion")
    ).with_columns(
        (
            pl.col("reconstructed_initial_max_excursion") - pl.col("max_excursion")
        ).alias("absolute_understatement")
    ).with_columns(
        (
            pl.col("absolute_understatement")
            / pl.col("reconstructed_initial_max_excursion")
        ).alias("relative_understatement"),
        pl.when(pl.col("side") == "HIGH")
        .then(
            pl.col("reconstructed_initial_max_price")
            > pl.col("max_price")
            + TOLERANCE * (1.0 + pl.col("reconstructed_initial_max_price").abs())
        )
        .otherwise(
            pl.col("reconstructed_initial_max_price")
            < pl.col("max_price")
            - TOLERANCE * (1.0 + pl.col("reconstructed_initial_max_price").abs())
        )
        .alias("materially_changed"),
    )
    inconsistent = result.filter(
        (pl.col("excursion_from_emitted_max_price") - pl.col("max_excursion")).abs()
        > TOLERANCE * (1.0 + pl.col("max_excursion").abs())
    ).height
    if inconsistent:
        raise ValueError(f"{inconsistent} emitted max_price/max_excursion pairs disagree")
    negative = result.filter(
        pl.col("absolute_understatement")
        < -TOLERANCE * (1.0 + pl.col("reconstructed_initial_max_excursion").abs())
    ).height
    if negative:
        raise ValueError(f"{negative} reconstructed excursions are below emitted values")
    non_source_first = result.filter(pl.col("first_excursion_ts_ns") >= pl.col("sweep_ts_ns")).height
    if non_source_first:
        raise ValueError(f"{non_source_first} first excursions are not earlier source minutes")
    return result


def finite_primary_control_population(raids: pl.DataFrame, destroyed: pl.DataFrame) -> int:
    """Reconstruct the existing future-destroy control's finite paired population."""
    paired = raids.select(
        "raid_id",
        "confirmation_ts_ns",
        "max_excursion_atr",
        "swing_atr",
        "strong_move",
    ).join(
        destroyed.select("raid_id", "swing_atr", "strong_move").rename(
            {
                "swing_atr": "destroyed_swing_atr",
                "strong_move": "destroyed_strong_move",
            }
        ),
        on="raid_id",
        how="inner",
        validate="1:1",
    )
    return paired.filter(
        pl.col("confirmation_ts_ns").is_not_null()
        & pl.col("max_excursion_atr").is_finite()
        & pl.col("swing_atr").is_finite()
        & pl.col("destroyed_swing_atr").is_finite()
        & pl.col("strong_move").is_not_null()
        & pl.col("destroyed_strong_move").is_not_null()
    ).height


def prevalence_counts(
    exposure: pl.DataFrame,
    *,
    all_raids: int,
    profile_undefined: int,
    primary_all: int,
    completed_all: int,
    control_population: int,
) -> list[dict[str, Any]]:
    """Build explicit numerator/denominator rows for verdict-relevant populations."""
    changed = exposure.filter(pl.col("materially_changed"))
    primary = exposure.filter(pl.col("primary_attribution"))
    primary_changed = primary.filter(pl.col("materially_changed"))
    completed = exposure.filter(pl.col("status") == "COMPLETED")
    completed_changed = completed.filter(pl.col("materially_changed"))

    def row(population: str, denominator: int, exposed: int, affected: int) -> dict[str, Any]:
        return {
            "population": population,
            "denominator_n": denominator,
            "atr_undefined_exposed_n": exposed,
            "atr_undefined_exposed_pct": 100.0 * exposed / denominator,
            "affected_n": affected,
            "affected_pct": 100.0 * affected / denominator,
        }

    rows = [
        row("all emitted raids", all_raids, exposure.height, changed.height),
        row(
            "all TPO-profile-undefined raids",
            profile_undefined,
            exposure.height,
            changed.height,
        ),
        row("ATR_UNDEFINED raids", exposure.height, exposure.height, changed.height),
        row("all primary-attributed raids", primary_all, primary.height, primary_changed.height),
        row("all completed raids", completed_all, completed.height, completed_changed.height),
    ]
    rows.append(
        {
            "population": "future-destroy aligned finite-primary pairs",
            "denominator_n": control_population,
            "atr_undefined_exposed_n": 0,
            "atr_undefined_exposed_pct": 0.0,
            "affected_n": 0,
            "affected_pct": 0.0,
            "excluded_atr_undefined_primary_n": primary.height,
            "excluded_affected_primary_n": primary_changed.height,
        }
    )
    return rows


def _distribution(frame: pl.DataFrame) -> dict[str, Any]:
    if frame.height == 0:
        return {"n": 0, "absolute": None, "relative": None}

    def stats(column: str) -> dict[str, float]:
        values = frame[column]
        result = {"mean": float(values.mean())}
        result.update(
            {f"q{int(q * 100):02d}": float(values.quantile(q, "nearest")) for q in QUANTILES}
        )
        return result

    return {
        "n": frame.height,
        "absolute": stats("absolute_understatement"),
        "relative": stats("relative_understatement"),
    }


def _layer_rows(exposure: pl.DataFrame, totals: pl.DataFrame, layer: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total_by_value = totals.group_by(layer).agg(pl.col("n_raids").sum().alias("all_raids_n"))
    for total in total_by_value.sort(layer).iter_rows(named=True):
        value = total[layer]
        subset = exposure.filter(pl.col(layer) == value)
        changed = subset.filter(pl.col("materially_changed"))
        rows.append(
            {
                "value": value,
                "all_raids_n": int(total["all_raids_n"]),
                "atr_undefined_n": subset.height,
                "atr_undefined_pct_of_all_raids": (
                    100.0 * subset.height / int(total["all_raids_n"])
                ),
                "affected_n": changed.height,
                "affected_pct_of_atr_undefined": (
                    100.0 * changed.height / subset.height if subset.height else None
                ),
                "zero_impact_n": subset.height - changed.height,
                "affected_distribution": _distribution(changed),
            }
        )
    return rows


def main() -> None:
    exposures: list[pl.DataFrame] = []
    totals: list[dict[str, Any]] = []
    profile_undefined = 0
    atr_profile_undefined = 0
    primary_all = 0
    completed_all = 0
    control_population = 0

    cell_dirs = sorted(path for path in ROOT.iterdir() if path.is_dir())
    for cell_dir in cell_dirs:
        ident = parse_cell(cell_dir.name)
        raids = pl.read_parquet(cell_dir / "raids.parquet", columns=RAID_COLUMNS)
        profiles = pl.read_parquet(
            cell_dir / "tpo_profiles.parquet",
            columns=["raid_id", "profile_status", "undefined_reason"],
        )
        destroyed = pl.read_parquet(
            cell_dir / "raids_destroyed.parquet",
            columns=["raid_id", "swing_atr", "strong_move"],
        )
        marks = pl.read_parquet(
            cell_dir / "bar_marks.parquet",
            columns=["ts_event_ns", "RealHigh", "RealLow"],
        )
        undefined = profiles.filter(pl.col("profile_status") == "UNDEFINED")
        profile_undefined += undefined.height
        atr_profile_undefined += undefined.filter(
            pl.col("undefined_reason") == "ATR_UNDEFINED"
        ).height
        primary_all += raids.filter(pl.col("primary_attribution")).height
        completed_all += raids.filter(pl.col("status") == "COMPLETED").height
        control_population += finite_primary_control_population(raids, destroyed)
        totals.append({**ident, "n_raids": raids.height})
        exposure = reconstruct_exposure(raids, profiles, marks).with_columns(
            *[pl.lit(value).alias(key) for key, value in ident.items()]
        )
        exposures.append(exposure)

    exposure = pl.concat(exposures)
    totals_frame = pl.DataFrame(totals)
    all_raids = int(totals_frame["n_raids"].sum())
    if exposure.height != atr_profile_undefined:
        raise ValueError("family ATR_UNDEFINED raid/profile totals disagree")

    changed = exposure.filter(pl.col("materially_changed"))
    unique_keys = ["instrument", "timeframe", "confirm_ref", "config", "raid_id"]
    report = {
        "analysis": "EXP-100 ATR_UNDEFINED initial-observation maximum-excursion defect",
        "boundary_statement": (
            "No final verdict, strategy change, rerun, tradability claim, or family action. "
            "Observed quantities come only from the frozen emissions."
        ),
        "zero_cost_disclosure": (
            "ZERO-COST-DISCLOSURE\n"
            "  cost_model: NO_COST_CHARGED\n"
            "  spread: not modeled\n"
            "  commissions: not modeled\n"
            "  swaps/funding: not modeled\n"
            "  implication: every figure in this document is gross and cost-free; no spread,\n"
            "    commission, or swap enters any calculation. Realised results would differ\n"
            "    (likely worse) under any real cost schedule.\n"
            "  prohibited_claims: fully-net, cost-complete, tradable, deployable\n"
            "  lifting: only an explicit operator directive may introduce a cost model for a\n"
            "    scoped experiment; the directive is recorded in that experiment's design.md."
        ),
        "source_boundary": {
            "rerun": False,
            "strategy_code_changed": False,
            "emissions": [
                "data/nautilus_runs/EXP-100/full/*/raids.parquet",
                "data/nautilus_runs/EXP-100/full/*/tpo_profiles.parquet",
                "data/nautilus_runs/EXP-100/full/*/bar_marks.parquet",
                "data/nautilus_runs/EXP-100/full/*/raids_destroyed.parquet",
            ],
            "cells": len(cell_dirs),
        },
        "definitions": {
            "exposed": (
                "raid profile_undefined_reason=ATR_UNDEFINED and matching TPO profile "
                "status/reason UNDEFINED/ATR_UNDEFINED"
            ),
            "reconstructed_initial_maximum": (
                "side-aware RealHigh/RealLow on the emitted completed observation mark "
                "joined at sweep_ts_ns"
            ),
            "absolute_understatement": "reconstructed excursion - emitted max_excursion",
            "relative_understatement": "absolute understatement / reconstructed excursion",
            "materially_changed": (
                "side-aware reconstructed max_price exceeds emitted max_price by more than "
                "1e-12 * (1 + abs(reconstructed max_price)); numerical materiality only, "
                "not an economic threshold"
            ),
        },
        "identifiability": {
            "exactly_identifiable": (
                "exposure, the completed initial-observation maximum, whether a later source "
                "minute exceeded the emitted first-minute extreme, and the understatement"
            ),
            "not_identifiable": (
                "the full source-minute path, the exact minute attaining the reconstructed maximum, "
                "and any still-later maximum after the initial completed observation; individual "
                "source minutes were not emitted"
            ),
            "why_later_is_identified": (
                "first_excursion_ts_ns is the first source minute beyond the level; when the "
                "completed observation extreme is larger, that larger extreme must occur later"
            ),
        },
        "population_prevalence": prevalence_counts(
            exposure,
            all_raids=all_raids,
            profile_undefined=profile_undefined,
            primary_all=primary_all,
            completed_all=completed_all,
            control_population=control_population,
        ),
        "impact": {
            "atr_undefined_n": exposure.height,
            "materially_changed_n": changed.height,
            "zero_impact_n": exposure.height - changed.height,
            "materially_changed_pct_of_atr_undefined": 100.0 * changed.height / exposure.height,
            "method_deduplicated_atr_undefined_n": exposure.unique(subset=unique_keys).height,
            "method_deduplicated_materially_changed_n": changed.unique(subset=unique_keys).height,
            "all_exposed_distribution_including_zero": _distribution(exposure),
            "materially_changed_distribution": _distribution(changed),
        },
        "by_layer": {
            layer: _layer_rows(exposure, totals_frame, layer) for layer in LAYERS
        },
        "decision_impact": {
            "coverage_and_lifecycle_counts": (
                "include these raid rows as count/state objects; chronology, identity, attribution, "
                "completion, and TPO-undefined counts do not depend on corrected max values"
            ),
            "max_excursion_identity_checks": (
                "raw max_excursion_bps self-reconciliation includes ATR-undefined rows but only "
                "re-derives the biased field; finite-ATR and strong_move checks exclude them"
            ),
            "future_destroy": (
                "excludes all ATR-undefined rows because max_excursion_atr is null; 112 exposed "
                "primary rows, including 84 affected completed rows, are outside its finite-primary "
                "population, so its published result is numerically unchanged"
            ),
            "hypothesis": (
                "the small all-raid prevalence does not restore exact max-excursion integrity: "
                "780/868 exposed rows are understated. Unaffected count/lifecycle/control findings "
                "stand, while max_price/max_excursion and descendants remain invalid for this subset"
            ),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["population_prevalence"], indent=2))
    print(json.dumps(report["impact"], indent=2))


if __name__ == "__main__":
    main()
