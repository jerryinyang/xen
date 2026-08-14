"""EXP-100 amendment-completeness and future-destroy interrogation.

Analyst-owned: reads raw emissions directly and uses ``xen.evaluation`` only for
canonical block-bootstrap intervals. No experiment-local code is imported.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from xen.evaluation import block_bootstrap_ci

REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "data/nautilus_runs/EXP-100/full"
OUT = REPO / "python/experiments/EXP-100/results/analysis"
INTEGRITY_Z = 2.8
BOOT_REPS = 500
BOOT_SEEDS = 5
EXPECTED_CONFIGS = {
    "PREVIOUS_1H", "PREVIOUS_4H", "PREVIOUS_1D", "PREVIOUS_1W",
    "PREVIOUS_ASIA", "PREVIOUS_EUROPE", "PREVIOUS_AMERICA",
    "ROLLING_7", "ROLLING_14", "ROLLING_22", "ROLLING_252",
}


def _identity_fail(actual: pl.Series, expected: pl.Series) -> int:
    finite = actual.is_finite() & expected.is_finite()
    if not finite.any():
        return 0
    tolerance = 1e-9 * (1.0 + expected.abs())
    return int(((actual - expected).abs() > tolerance).filter(finite).sum())


def _bootstrap_se(x: np.ndarray, *, block: int = 5) -> float:
    """Median circular-block bootstrap SE across a fixed seed battery."""
    n = len(x)
    if n < 2:
        return 0.0
    block = max(1, min(block, n - 1))
    n_blocks = int(np.ceil(n / block))
    ses = []
    for seed in range(BOOT_SEEDS):
        rng = np.random.default_rng(41 + seed)
        means = np.empty(BOOT_REPS)
        for draw in range(BOOT_REPS):
            starts = rng.integers(0, n, size=n_blocks)
            idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n] % n
            means[draw] = float(x[idx].mean())
        ses.append(float(means.std(ddof=1)))
    return float(np.median(ses))


def _ci_rows(x: np.ndarray) -> list[dict[str, Any]]:
    return [
        {"block_requested": block, **block_bootstrap_ci(
            x, block=block, n_boot=BOOT_REPS, seed=101, n_seeds=BOOT_SEEDS
        )}
        for block in (2, 5, 10)
    ]


def _parse(cell_id: str) -> dict[str, str]:
    parts = cell_id.split("-")
    return {
        "cell_id": cell_id,
        "symbol": parts[1].upper(),
        "timeframe": parts[2],
        "method": parts[3],
        "confirm_ref": parts[4],
        "level_config": "_".join(parts[5:]).upper(),
    }


def _control_row(path: Path, ident: dict[str, str]) -> dict[str, Any]:
    raw = pl.read_parquet(
        path / "raids.parquet",
        columns=[
            "raid_id", "level_id", "confirmation_ts_ns", "max_excursion_atr",
            "swing_atr", "strong_move", "pre_mfe_retrace",
        ],
    )
    destroyed = pl.read_parquet(
        path / "raids_destroyed.parquet",
        columns=["raid_id", "swing_atr", "strong_move", "pre_mfe_retrace"],
    ).rename({
        "swing_atr": "destroyed_swing_atr",
        "strong_move": "destroyed_strong_move",
        "pre_mfe_retrace": "destroyed_pre_mfe_retrace",
    })
    paired = raw.join(destroyed, on="raid_id", how="inner").filter(
        pl.col("confirmation_ts_ns").is_not_null()
        & pl.col("max_excursion_atr").is_finite()
        & pl.col("swing_atr").is_finite()
        & pl.col("destroyed_swing_atr").is_finite()
        & pl.col("strong_move").is_not_null()
        & pl.col("destroyed_strong_move").is_not_null()
    ).with_columns(
        (pl.col("strong_move") == (pl.col("swing_atr") > pl.col("max_excursion_atr")))
        .cast(pl.Float64).alias("raw_alignment"),
        (
            pl.col("destroyed_strong_move")
            == (pl.col("destroyed_swing_atr") > pl.col("max_excursion_atr"))
        ).cast(pl.Float64).alias("destroyed_alignment"),
        (pl.col("swing_atr") - pl.col("destroyed_swing_atr")).abs()
        .alias("abs_swing_change"),
        pl.col("swing_atr").abs().alias("abs_raw_swing"),
    ).with_columns(
        (pl.col("raw_alignment") - pl.col("destroyed_alignment"))
        .alias("alignment_collapse")
    )
    clusters = paired.group_by("level_id").agg(
        pl.col("alignment_collapse").mean().alias("alignment_collapse")
    ).sort("level_id")
    values = clusters["alignment_collapse"].to_numpy().astype(float)
    cis = _ci_rows(values)
    main_ci = cis[1]
    bootstrap_se = _bootstrap_se(values)
    raw_alignment = float(paired["raw_alignment"].mean())
    destroyed_alignment = float(paired["destroyed_alignment"].mean())
    collapse = raw_alignment - destroyed_alignment
    mean_abs_change = float(paired["abs_swing_change"].mean())
    mean_abs_raw = float(paired["abs_raw_swing"].mean())
    retrace_changed = paired.filter(
        (pl.col("pre_mfe_retrace") != pl.col("destroyed_pre_mfe_retrace"))
        | (
            pl.col("pre_mfe_retrace").is_null()
            != pl.col("destroyed_pre_mfe_retrace").is_null()
        )
    ).height
    raw_alignment_n = int(paired["raw_alignment"].sum())
    destroyed_alignment_n = int(paired["destroyed_alignment"].sum())
    return {
        **ident,
        "control_population": "aligned_finite_primary_raid_pairs",
        "aligned_pair_denominator_n": paired.height,
        "aligned_level_cluster_n": clusters.height,
        "raw_alignment_numerator_n": raw_alignment_n,
        "destroyed_alignment_numerator_n": destroyed_alignment_n,
        "raw_alignment_fraction": raw_alignment,
        "destroyed_alignment_fraction": destroyed_alignment,
        "destroyed_alignment_survival_fraction": destroyed_alignment / raw_alignment,
        "alignment_collapse_fraction": collapse / raw_alignment,
        "alignment_collapse_ci_low": main_ci["ci"][0],
        "alignment_collapse_ci_high": main_ci["ci"][1],
        "alignment_collapse_ci_low_seed_min": main_ci["ci_low_seed_range"][0],
        "alignment_collapse_ci_low_seed_max": main_ci["ci_low_seed_range"][1],
        "alignment_collapse_bootstrap_se": bootstrap_se,
        "integrity_bite": INTEGRITY_Z * bootstrap_se,
        "integrity_pass": collapse >= INTEGRITY_Z * bootstrap_se,
        "block_sensitivity_json": json.dumps(cis, sort_keys=True),
        "block_ci_low_min": min(row["ci"][0] for row in cis),
        "block_ci_low_max": max(row["ci"][0] for row in cis),
        "block_fragile": min(row["ci"][0] for row in cis) <= 0.0,
        "mean_abs_swing_change": mean_abs_change,
        "mean_abs_raw_swing": mean_abs_raw,
        "swing_perturbation_fraction": (
            mean_abs_change / mean_abs_raw if mean_abs_raw else None
        ),
        "retrace_changed_n": retrace_changed,
        "retrace_changed_fraction": retrace_changed / paired.height,
    }


def _audit_cell(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ident = _parse(path.name)
    meta = json.loads((path / "run_metadata.json").read_text(encoding="utf-8"))
    cfg = meta["run_config"]["cell"]
    raids = pl.read_parquet(path / "raids.parquet")
    marks = pl.read_parquet(path / "bar_marks.parquet")
    tpo = pl.read_parquet(path / "tpo_profiles.parquet")

    retrace = raids.select(
        "side", "primary_attribution", "confirmation_ts_ns", "confirmation_price",
        pl.col("pre_mfe_retrace").struct.field("price").alias("retrace_price"),
        pl.col("pre_mfe_retrace").struct.field("status").alias("retrace_status"),
    )
    retrace_defined = retrace.filter(pl.col("retrace_status").is_not_null())
    retrace_side_bound_fail = retrace_defined.filter(
        ((pl.col("side") == "HIGH") & (pl.col("retrace_price") < pl.col("confirmation_price")))
        | ((pl.col("side") == "LOW") & (pl.col("retrace_price") > pl.col("confirmation_price")))
    ).height
    no_mfe_price_fail = retrace_defined.filter(
        (pl.col("retrace_status") == "NO_POST_CONFIRMATION_MFE")
        & ((pl.col("retrace_price") - pl.col("confirmation_price")).abs() > 1e-12)
    ).height

    duration_end = pl.when(pl.col("return_ts_ns").is_not_null()).then(
        pl.col("return_ts_ns")
    ).otherwise(pl.col("endpoint_ts_ns"))
    expected_excursion_duration = duration_end - pl.col("first_excursion_ts_ns")
    expected_swing_duration = pl.col("endpoint_ts_ns") - pl.col("confirmation_ts_ns")
    excursion_duration_fail = raids.filter(
        pl.col("excursion_duration_ns") != expected_excursion_duration
    ).height
    swing_duration_fail = raids.filter(
        pl.col("confirmation_ts_ns").is_not_null()
        & (pl.col("swing_duration_ns") != expected_swing_duration)
    ).height
    unconfirmed_swing_duration_nonnull = raids.filter(
        pl.col("confirmation_ts_ns").is_null()
        & pl.col("swing_duration_ns").is_not_null()
    ).height
    duration_alias_fail = raids.filter(
        (pl.col("duration_ns") != pl.col("swing_duration_ns"))
        | (pl.col("duration_ns").is_null() != pl.col("swing_duration_ns").is_null())
    ).height

    finite_atr = raids.filter(
        pl.col("raid_atr").is_finite() & (pl.col("raid_atr") > 0)
        & pl.col("max_excursion_atr").is_finite()
    )
    max_exc_atr_fail = _identity_fail(
        finite_atr["max_excursion_atr"],
        finite_atr["max_excursion"] / finite_atr["raid_atr"],
    )
    max_exc_bps_fail = _identity_fail(
        raids["max_excursion_bps"],
        raids["max_excursion"] / raids["level_price"].abs() * 10_000.0,
    )
    finite_swing = raids.filter(
        pl.col("raid_atr").is_finite() & (pl.col("raid_atr") > 0)
        & pl.col("swing_atr").is_finite()
    )
    swing_atr_fail = _identity_fail(
        finite_swing["swing_atr"], finite_swing["swing_price"] / finite_swing["raid_atr"]
    )
    strong_move_fail = finite_swing.filter(
        pl.col("strong_move") != (pl.col("swing_atr") > pl.col("max_excursion_atr"))
    ).height

    defined_tpo = tpo.filter(pl.col("profile_status") == "DEFINED")
    bin_width_fail = _identity_fail(
        defined_tpo["bin_width"], defined_tpo["atr_unit"] * 0.10
    )
    va_width_fail = _identity_fail(
        defined_tpo["va_width"], defined_tpo["vah"] - defined_tpo["val"]
    )
    gap_atr_fail = _identity_fail(
        defined_tpo["gap_span_atr"], defined_tpo["gap_span"] / defined_tpo["atr_unit"]
    )
    gap_va_fail = _identity_fail(
        defined_tpo["gap_span_va"], defined_tpo["gap_span"] / defined_tpo["va_width"]
    )
    tight_fail = defined_tpo.filter(
        pl.col("tight_gap") != (pl.col("gap_span") < 0.50 * pl.col("va_width"))
    ).height

    primary = raids.filter(pl.col("primary_attribution"))
    primary_group_max = primary.group_by(["confirmation_ts_ns", "side"]).len()["len"].max()
    primary_status_fail = primary.filter(
        ~pl.col("status").is_in(["COMPLETED", "RIGHT_CENSORED_ENDPOINT"])
    ).height
    completed_nonprimary = raids.filter(
        (pl.col("status") == "COMPLETED") & ~pl.col("primary_attribution")
    ).height
    nonprimary = raids.filter(pl.col("status") == "CONFIRMED_NON_PRIMARY")
    primary_keys = primary.select(
        pl.col("confirmation_ts_ns").alias("settlement_ts_ns"), "side"
    ).unique()
    nonprimary_unlinked = nonprimary.join(
        primary_keys,
        left_on=["endpoint_ts_ns", "side"],
        right_on=["settlement_ts_ns", "side"],
        how="anti",
    ).height

    obs_minutes = int(cfg["observation_minutes"])
    source_sum = int(marks["source_bars"].sum())
    processed_source = int(meta["state_snapshot"]["processed_source_bars"])
    invalid_source_count = marks.filter(
        (pl.col("source_bars") <= 0) | (pl.col("source_bars") > obs_minutes)
    ).height
    mark_interval_min = int(marks.sort("SourceCloseTime")["SourceCloseTime"].diff().drop_nulls().min())

    years = raids.with_columns(
        pl.from_epoch("sweep_ts_ns", time_unit="ns").dt.year().alias("year")
    ).group_by("year").agg(
        pl.len().alias("n_raids"),
        pl.col("primary_attribution").sum().alias("n_primary"),
        (pl.col("status") == "COMPLETED").sum().alias("n_completed"),
    ).sort("year")
    year_rows = [{**ident, **row} for row in years.to_dicts()]

    row = {
        **ident,
        "n_raids": raids.height,
        "n_levels_in_metadata": int(meta["state_snapshot"]["open_levels"]),
        "n_marks": marks.height,
        "n_source_minutes": processed_source,
        "n_source_minutes_in_complete_observations": source_sum,
        "source_minutes_not_emitted_in_complete_observations": processed_source - source_sum,
        "invalid_observation_source_count": invalid_source_count,
        "minimum_mark_interval_ns": mark_interval_min,
        "config_matches_cell_id": (
            cfg["archive_symbol"] == ident["symbol"]
            and f"{cfg['observation_minutes']}m" == ident["timeframe"]
            and cfg["confirmation_method"].lower() == ident["method"]
            and cfg["confirmation_reference"].lower() == ident["confirm_ref"]
            and cfg["level_config"] == ident["level_config"]
        ),
        "level_config_current": cfg["level_config"] in EXPECTED_CONFIGS,
        "confirmation_grid_ok": (
            (obs_minutes in (15, 30) and cfg["confirmation_reference"] == "1H")
            or (obs_minutes == 60 and cfg["confirmation_reference"] in ("1H", "4H"))
        ),
        "max_excursion_atr_identity_fail": max_exc_atr_fail,
        "max_excursion_bps_identity_fail": max_exc_bps_fail,
        "swing_atr_identity_fail": swing_atr_fail,
        "strong_move_identity_fail": strong_move_fail,
        "excursion_duration_fail": excursion_duration_fail,
        "swing_duration_fail": swing_duration_fail,
        "unconfirmed_swing_duration_nonnull": unconfirmed_swing_duration_nonnull,
        "duration_alias_fail": duration_alias_fail,
        "primary_group_max": int(primary_group_max or 0),
        "primary_status_fail": primary_status_fail,
        "completed_nonprimary": completed_nonprimary,
        "nonprimary_unlinked_to_primary_confirmation": nonprimary_unlinked,
        "retrace_side_bound_fail": retrace_side_bound_fail,
        "retrace_no_mfe_price_fail": no_mfe_price_fail,
        "retrace_defined_n": retrace_defined.filter(pl.col("retrace_status") == "DEFINED").height,
        "retrace_ambiguous_n": retrace_defined.filter(
            pl.col("retrace_status") == "AMBIGUOUS_SAME_BAR"
        ).height,
        "retrace_no_mfe_n": retrace_defined.filter(
            pl.col("retrace_status") == "NO_POST_CONFIRMATION_MFE"
        ).height,
        "tpo_bin_width_fail": bin_width_fail,
        "tpo_va_width_fail": va_width_fail,
        "tpo_gap_atr_fail": gap_atr_fail,
        "tpo_gap_va_fail": gap_va_fail,
        "tpo_tight_rule_fail": tight_fail,
        "tpo_va_mass_short": defined_tpo.filter(pl.col("va_mass") < 0.70 - 1e-12).height,
        "tpo_conservation_fail": defined_tpo.filter(
            ~pl.col("tpo_conservation_ok")
        ).height,
    }
    return row, year_rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    year_rows: list[dict[str, Any]] = []
    for path in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        audit, years = _audit_cell(path)
        audit_rows.append(audit)
        year_rows.extend(years)
        control_rows.append(_control_row(path, _parse(path.name)))

    audit = pl.DataFrame(audit_rows).sort("cell_id")
    control = pl.DataFrame(control_rows).sort("cell_id")
    years = pl.DataFrame(year_rows).sort(["cell_id", "year"])
    audit.write_csv(OUT / "amendment_audit_by_cell.csv")
    control.write_csv(OUT / "destroy_alignment_by_cell.csv")
    years.write_csv(OUT / "coverage_by_cell_year.csv")

    numeric_fail_cols = [
        "invalid_observation_source_count", "max_excursion_atr_identity_fail",
        "max_excursion_bps_identity_fail", "swing_atr_identity_fail",
        "strong_move_identity_fail", "excursion_duration_fail", "swing_duration_fail",
        "unconfirmed_swing_duration_nonnull", "duration_alias_fail", "primary_status_fail",
        "completed_nonprimary", "nonprimary_unlinked_to_primary_confirmation",
        "retrace_side_bound_fail", "retrace_no_mfe_price_fail", "tpo_bin_width_fail",
        "tpo_va_width_fail", "tpo_gap_atr_fail", "tpo_gap_va_fail",
        "tpo_tight_rule_fail", "tpo_va_mass_short", "tpo_conservation_fail",
    ]
    summary = {
        "n_cells": audit.height,
        "all_config_matches_cell_id": bool(audit["config_matches_cell_id"].all()),
        "all_level_configs_current": bool(audit["level_config_current"].all()),
        "all_confirmation_grids_current": bool(audit["confirmation_grid_ok"].all()),
        "max_primary_per_confirmation_side": int(audit["primary_group_max"].max()),
        "failure_sums": {name: int(audit[name].sum()) for name in numeric_fail_cols},
        "source_minutes_not_in_complete_observations": int(
            audit["source_minutes_not_emitted_in_complete_observations"].sum()
        ),
        "year_range": [int(years["year"].min()), int(years["year"].max())],
        "year_totals": years.group_by("year").agg(
            pl.col("n_raids").sum(), pl.col("n_primary").sum(), pl.col("n_completed").sum()
        ).sort("year").to_dicts(),
        "pre_mfe_status_totals": {
            "DEFINED": int(audit["retrace_defined_n"].sum()),
            "AMBIGUOUS_SAME_BAR": int(audit["retrace_ambiguous_n"].sum()),
            "NO_POST_CONFIRMATION_MFE": int(audit["retrace_no_mfe_n"].sum()),
        },
        "control": {
            "all_264_integrity_pass": bool(control["integrity_pass"].all()),
            "n_integrity_pass": int(control["integrity_pass"].sum()),
            "population": "264 cell-level summaries of aligned finite primary raid pairs",
            "aligned_pair_denominator_range": [
                int(control["aligned_pair_denominator_n"].min()),
                int(control["aligned_pair_denominator_n"].max()),
            ],
            "aligned_level_cluster_range": [
                int(control["aligned_level_cluster_n"].min()),
                int(control["aligned_level_cluster_n"].max()),
            ],
            "alignment_collapse_fraction_definition": (
                "(raw_alignment_fraction - destroyed_alignment_fraction) / "
                "raw_alignment_fraction"
            ),
            "destroyed_alignment_survival_fraction_definition": (
                "destroyed_alignment_fraction / raw_alignment_fraction"
            ),
            "alignment_fraction_denominator": "aligned_pair_denominator_n",
            "alignment_collapse_fraction_range": [
                float(control["alignment_collapse_fraction"].min()),
                float(control["alignment_collapse_fraction"].max()),
            ],
            "alignment_collapse_fraction_median": float(
                control["alignment_collapse_fraction"].median()
            ),
            "alignment_collapse_ci_low_range": [
                float(control["alignment_collapse_ci_low"].min()),
                float(control["alignment_collapse_ci_low"].max()),
            ],
            "alignment_collapse_ci_low_seed_range_global": [
                float(control["alignment_collapse_ci_low_seed_min"].min()),
                float(control["alignment_collapse_ci_low_seed_max"].max()),
            ],
            "destroyed_alignment_survival_fraction_range": [
                float(control["destroyed_alignment_survival_fraction"].min()),
                float(control["destroyed_alignment_survival_fraction"].max()),
            ],
            "swing_perturbation_fraction_range": [
                float(control["swing_perturbation_fraction"].min()),
                float(control["swing_perturbation_fraction"].max()),
            ],
            "retrace_changed_fraction_range": [
                float(control["retrace_changed_fraction"].min()),
                float(control["retrace_changed_fraction"].max()),
            ],
            "block_fragile_cells": int(control["block_fragile"].sum()),
        },
    }
    (OUT / "amendment_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
