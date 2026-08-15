from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Callable


def test_exp101_adapter_emits_every_registered_channel_and_sensitivity(
    load_exp_module: Callable[[str], ModuleType], tmp_path: Path
) -> None:
    module = load_exp_module("EXP-101")
    adapter = module.Adapter(n_boot=40, n_destroy=20, seeds=(0, 1))
    frame = adapter.fixture_frame()
    assert adapter.integrity(frame).blocking_pass
    rows = adapter.analyze(frame)
    assert {row["channel"] for row in rows} == {
        "swing_price",
        "swing_bps",
        "swing_atr",
        "swing_duration_ns",
        "strong_move",
    }
    assert all(set(row["sensitivities"]) == {"2", "5", "10"} for row in rows)
    assert {(row["arm"], row["comparator"]) for row in rows} == {
        ("PREVIOUS_4H", "PREVIOUS_1H"),
        ("PREVIOUS_1D", "PREVIOUS_1H"),
        ("PREVIOUS_1W", "PREVIOUS_1H"),
        ("PREVIOUS_EUROPE", "PREVIOUS_ASIA"),
        ("PREVIOUS_AMERICA", "PREVIOUS_ASIA"),
        ("ROLLING_14", "ROLLING_7"),
        ("ROLLING_22", "ROLLING_7"),
        ("ROLLING_252", "ROLLING_7"),
    }
    assert all(
        set(row["stratum"])
        == {
            "archive_symbol",
            "timeframe",
            "confirmation_method",
            "confirmation_reference",
            "side",
        }
        for row in rows
    )
    assert all(set(row) >= {"observed", "ideal", "interpretation"} for row in rows)
    extra = adapter.extra(frame)
    assert {row["channel"] for row in extra["control"]["records"]} == {
        "swing_atr",
        "swing_duration_ns",
        "strong_move",
    }
    assert extra["control"]["fixed_points"] == 0
    assert extra["control"]["population_match"] is True
    assert set(extra["census"]) >= {"arm", "comparator", "status", "missingness"}


def test_exp101_control_null_class_is_exactly_five_bits(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-101")
    row = {
        "swing_price": 1.0,
        "swing_bps": None,
        "swing_atr": 2.0,
        "swing_duration_ns": None,
        "strong_move": True,
        "profile_status": "SHOULD_NOT_GROUP",
        "profile_undefined_reason": "SHOULD_NOT_GROUP",
    }
    assert module.control_null_class(row) == (False, True, False, True, False)
