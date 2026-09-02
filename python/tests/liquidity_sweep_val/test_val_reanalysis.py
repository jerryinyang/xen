from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl


ROOT = Path(__file__).parents[2]


def load_module(val_id: str):
    path = ROOT / "experiments" / val_id / "analysis_code" / "interrogate.py"
    spec = importlib.util.spec_from_file_location(val_id, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selection_summary_counts_primary_competition_and_exact_repeat():
    module = load_module("VAL-009")
    frame = pl.DataFrame(
        {
            "status": ["COMPLETED", "CONFIRMED_NON_PRIMARY", "FAILED_BREAKOUT"],
            "confirmation_ts_ns": [10, 10, None],
            "endpoint_ts_ns": [20, 10, 12],
            "primary_attribution": [True, False, False],
            "prior_raid_count": [0, 1, 2],
            "sweep_ts_ns": [7, 6, 5],
            "level_creation_ts_ns": [1, 1, 1],
        }
    )
    result = module.selection_summary(frame)
    assert result["status_counts"] == {"COMPLETED": 1, "CONFIRMED_NON_PRIMARY": 1, "FAILED_BREAKOUT": 1}
    assert result["competition_sets"]["sets_with_competition"] == 1
    assert result["exact_repeat_count"]["0"] == 1


def test_selection_summary_does_not_merge_competition_sets_from_different_source_cells():
    module = load_module("VAL-009")
    frame = pl.DataFrame(
        {
            "source_cell": ["cell-a", "cell-b"],
            "status": ["COMPLETED", "COMPLETED"],
            "confirmation_ts_ns": [10, 10],
            "endpoint_ts_ns": [20, 20],
            "primary_attribution": [True, True],
            "prior_raid_count": [0, 0],
            "sweep_ts_ns": [7, 7],
            "level_creation_ts_ns": [1, 1],
        }
    )
    result = module.selection_summary(frame)
    assert result["competition_sets"]["n_sets"] == 2
    assert result["competition_sets"]["sets_with_competition"] == 0


def test_selection_summary_links_non_primary_terminal_to_primary_confirmation():
    module = load_module("VAL-009")
    frame = pl.DataFrame(
        {
            "source_cell": ["cell-a", "cell-a"],
            "side": ["HIGH", "HIGH"],
            "status": ["COMPLETED", "CONFIRMED_NON_PRIMARY"],
            "confirmation_ts_ns": [10, None],
            "endpoint_ts_ns": [20, 10],
            "primary_attribution": [True, False],
            "prior_raid_count": [1, 0],
            "sweep_ts_ns": [7, 6],
            "level_creation_ts_ns": [1, 1],
        }
    )
    result = module.selection_summary(frame)
    assert result["competition_sets"]["n_sets"] == 1
    assert result["competition_sets"]["sets_with_competition"] == 1
    assert result["competition_sets"]["sets_with_exactly_one_primary"] == 1


def test_anatomy_summary_decomposes_the_strong_move_inequality():
    module = load_module("VAL-010")
    frame = pl.DataFrame(
        {
            "max_excursion_atr": [1.0, 2.0],
            "swing_atr": [3.0, 1.0],
            "strong_move": [True, False],
            "swing_duration_ns": [10, 20],
            "pre_mfe_retrace": [{"price": 1.0, "status": "DEFINED"}, {"price": 2.0, "status": "NO_POST_CONFIRMATION_MFE"}],
        }
    )
    result = module.anatomy_summary(frame)
    assert result["n"] == 2
    assert result["mean_surplus_atr"] == 0.5
    assert result["strong_move_rate"] == 0.5
    assert result["retrace_status_counts"]["DEFINED"] == 1


def test_anatomy_source_projection_keeps_the_train_fence_timestamp():
    module = load_module("VAL-010")
    assert "sweep_ts_ns" in module.OUTCOME_COLUMNS


def test_anatomy_by_repeat_band_keeps_all_three_registered_repeat_views():
    module = load_module("VAL-010")
    frame = pl.DataFrame(
        {
            "config": ["ROLLING_7", "ROLLING_7", "ROLLING_7"],
            "prior_raid_count": [0, 1, 2],
            "max_excursion_atr": [1.0, 1.0, 1.0],
            "swing_atr": [2.0, 3.0, 4.0],
            "strong_move": [True, True, True],
            "swing_duration_ns": [10, 20, 30],
            "pre_mfe_retrace": [None, None, None],
        }
    )
    result = module.anatomy_by_repeat_band(frame)
    assert {row["repeat_band"] for row in result} == {"0", "1", "2+"}


def test_repeat_contrasts_keep_duration_separate_from_the_strong_move_rate():
    module = load_module("VAL-010")
    frame = pl.DataFrame(
        {
            "physical_cell": ["a", "a", "a"],
            "side": ["HIGH", "HIGH", "HIGH"],
            "config": ["ROLLING_7", "ROLLING_7", "ROLLING_7"],
            "prior_raid_count": [0, 1, 2],
            "max_excursion_atr": [1.0, 1.0, 1.0],
            "swing_atr": [3.0, 2.0, 1.0],
            "strong_move": [True, False, False],
            "swing_duration_ns": [10, 20, 30],
            "pre_mfe_retrace": [None, None, None],
        }
    )
    result = module.repeat_contrast_summary(frame)
    assert result["1_vs_0"]["strong_move_rate"]["n_strata"] == 1
    assert result["1_vs_0"]["strong_move_rate"]["n_negative"] == 1
    assert result["1_vs_0"]["duration_hours"]["mean_stratum_difference"] > 0


def test_frequency_summary_uses_all_raid_starts_not_completed_primary_rows():
    module = load_module("VAL-011")
    marks = pl.DataFrame({"ts_event_ns": [100, 200], "regime": ["MID", "MID"]})
    raids = pl.DataFrame({"sweep_ts_ns": [200, 200], "side": ["LOW", "HIGH"], "raid_id": ["a", "b"]})
    result = module.frequency_summary(marks, raids)
    assert result["MID"]["exposure"] == 1
    assert result["MID"]["starts"] == 2
    assert result["MID"]["rate_per_1000_marks"] == 2000.0


def test_canonical_source_cells_collapse_only_the_bb_lc_method_pair():
    module = load_module("VAL-011")
    cells = [
        "ctrader-eurusd-15m-breakout_bar-1h-rolling_7",
        "ctrader-eurusd-15m-level_close-1h-rolling_7",
        "ctrader-eurusd-15m-breakout_bar-4h-rolling_7",
    ]
    assert module.canonical_source_cells(cells) == [
        "ctrader-eurusd-15m-breakout_bar-1h-rolling_7",
        "ctrader-eurusd-15m-breakout_bar-4h-rolling_7",
    ]


def test_regime_source_projection_keeps_duration():
    module = load_module("VAL-011")
    assert "swing_duration_ns" in module.RAID_COLUMNS


def test_regime_contrasts_keep_atr_duration_and_strong_move_separate():
    module = load_module("VAL-011")
    raids = pl.DataFrame(
        {
            "source_cell": ["a", "a", "a"],
            "side": ["HIGH", "HIGH", "HIGH"],
            "raid_regime": ["MID", "LOW", "HIGH"],
            "swing_atr": [3.0, 2.0, 4.0],
            "strong_move": [True, False, True],
            "swing_duration_ns": [20, 10, 30],
        }
    )
    result = module.regime_contrast_summary(raids)
    assert result["LOW_vs_MID"]["swing_atr"]["n_negative"] == 1
    assert result["HIGH_vs_MID"]["duration_hours"]["n_positive"] == 1
