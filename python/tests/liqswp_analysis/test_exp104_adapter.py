from __future__ import annotations

from types import ModuleType
from typing import Callable


def test_exp104_emits_regime_contrasts_frequency_and_join_evidence(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    adapter = module.Adapter(n_boot=40, n_destroy=2000, seeds=(0, 1))
    frame = adapter.fixture_frame()
    assert adapter.integrity(frame).blocking_pass
    rows = adapter.analyze(frame)
    assert {(row["arm"], row["comparator"]) for row in rows} == {
        ("LOW", "MID"),
        ("HIGH", "MID"),
    }
    assert {row["channel"] for row in rows} >= {
        "swing_atr",
        "swing_duration_ns",
        "strong_move",
    }
    extra = adapter.extra(frame)
    assert set(extra) >= {"frequency_census", "regime_census", "profile_join", "control"}
    assert extra["profile_join"]["unmatched_raids"] == 0


def test_frequency_blocks_dispatch_per_timeframe(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    """Per-timeframe one-day blocks must reach the registered L/2, L, 2L."""
    module = load_exp_module("EXP-104")
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["15m"] == (48, 96, 192)
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["30m"] == (24, 48, 96)
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["1h"] == (12, 24, 48)


def test_frequency_reports_warmup_undefined_and_observed_layers(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    marks = [
        {"ts_event_ns": 1, "regime": "LOW"},
        {"ts_event_ns": 2, "regime": "MID"},
        {"ts_event_ns": 3, "regime": "REGIME_WARMUP"},
        {"ts_event_ns": 4, "regime": "HIGH"},
    ]
    raids = [{"raid_id": "r1", "sweep_ts_ns": 2, "raid_regime": "LOW"}]
    result = module.frequency_rate(marks, raids, block_length=96)
    assert result["exposure"] == {"LOW": 1, "MID": 1, "HIGH": 0}
    assert result["rates_per_1000"]["LOW"] == 1000.0
    assert result["warmup_undefined_exposure"] == {"REGIME_WARMUP": 1}
    assert "HIGH" in result["empty_exposure"]


def test_frequency_uses_preceding_mark_and_reports_empty_exposure(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    marks = [
        {"ts_event_ns": 1, "regime": "LOW"},
        {"ts_event_ns": 2, "regime": "MID"},
        {"ts_event_ns": 3, "regime": "MID"},
    ]
    raids = [{"raid_id": "r1", "sweep_ts_ns": 2, "raid_regime": "LOW"}]
    result = module.frequency_rate(marks, raids, block_length=96)
    assert result["exposure"] == {"LOW": 1, "MID": 1, "HIGH": 0}
    assert result["starts"] == {"LOW": 1, "MID": 0, "HIGH": 0}
    assert "HIGH" in result["empty_exposure"]
