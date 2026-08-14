from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import polars as pl
import pytest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "python/experiments/EXP-100/analysis_code/atr_undefined_prevalence.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("exp100_atr_undefined_prevalence", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic_emissions() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    raids = pl.DataFrame(
        {
            "raid_id": ["high-changed", "low-zero", "defined"],
            "side": ["HIGH", "LOW", "HIGH"],
            "level_price": [100.0, 100.0, 100.0],
            "sweep_ts_ns": [900, 1_800, 2_700],
            "first_excursion_ts_ns": [100, 1_000, 2_000],
            "max_price": [100.8, 99.5, 100.4],
            "max_excursion": [0.8, 0.5, 0.4],
            "profile_generation": [None, None, 1],
            "raid_atr": [None, None, 0.5],
            "profile_undefined_reason": ["ATR_UNDEFINED", "ATR_UNDEFINED", None],
            "primary_attribution": [True, False, False],
            "status": ["COMPLETED", "FAILED_BREAKOUT", "FAILED_BREAKOUT"],
        }
    )
    profiles = pl.DataFrame(
        {
            "raid_id": ["high-changed", "low-zero", "defined"],
            "profile_status": ["UNDEFINED", "UNDEFINED", "DEFINED"],
            "undefined_reason": ["ATR_UNDEFINED", "ATR_UNDEFINED", None],
        }
    )
    marks = pl.DataFrame(
        {
            "ts_event_ns": [900, 1_800, 2_700],
            "RealHigh": [101.2, 100.2, 100.4],
            "RealLow": [99.7, 99.5, 99.8],
        }
    )
    return raids, profiles, marks


def test_reconstruct_exposure_separates_zero_and_changed_values() -> None:
    module = _load()
    exposure = module.reconstruct_exposure(*_synthetic_emissions())

    assert exposure.height == 2
    changed = exposure.filter(pl.col("raid_id") == "high-changed").row(0, named=True)
    zero = exposure.filter(pl.col("raid_id") == "low-zero").row(0, named=True)
    assert changed["reconstructed_initial_max_excursion"] == pytest.approx(1.2)
    assert changed["absolute_understatement"] == pytest.approx(0.4)
    assert changed["relative_understatement"] == pytest.approx(1 / 3)
    assert changed["materially_changed"] is True
    assert zero["absolute_understatement"] == pytest.approx(0.0)
    assert zero["materially_changed"] is False


def test_finite_primary_control_population_excludes_atr_undefined_rows() -> None:
    module = _load()
    raids = pl.DataFrame(
        {
            "raid_id": ["included", "atr-undefined", "unconfirmed"],
            "confirmation_ts_ns": [1, 2, None],
            "max_excursion_atr": [0.5, None, 0.5],
            "swing_atr": [1.0, 1.0, 1.0],
            "strong_move": [True, None, True],
        }
    )
    destroyed = pl.DataFrame(
        {
            "raid_id": ["included", "atr-undefined", "unconfirmed"],
            "swing_atr": [0.8, 0.8, 0.8],
            "strong_move": [True, True, True],
        }
    )

    assert module.finite_primary_control_population(raids, destroyed) == 1


def test_prevalence_counts_use_explicit_population_denominators() -> None:
    module = _load()
    exposure = module.reconstruct_exposure(*_synthetic_emissions())

    rows = module.prevalence_counts(
        exposure,
        all_raids=10,
        profile_undefined=4,
        primary_all=5,
        completed_all=3,
        control_population=7,
    )
    by_population = {row["population"]: row for row in rows}

    assert by_population["all emitted raids"]["affected_n"] == 1
    assert by_population["all emitted raids"]["affected_pct"] == pytest.approx(10.0)
    assert by_population["all TPO-profile-undefined raids"]["affected_pct"] == pytest.approx(
        25.0
    )
    assert by_population["ATR_UNDEFINED raids"]["affected_pct"] == pytest.approx(50.0)
    assert by_population["all primary-attributed raids"]["atr_undefined_exposed_n"] == 1
    assert by_population["all completed raids"]["affected_n"] == 1
    control = by_population["future-destroy aligned finite-primary pairs"]
    assert control["affected_n"] == 0
    assert control["excluded_affected_primary_n"] == 1
