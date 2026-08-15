from __future__ import annotations

from types import ModuleType
from typing import Callable


def test_count_band_derivation_does_not_mutate_source(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-102")
    source = {"prior_raid_count": 3, "raid_id": "R0"}
    derived = module.with_count_band(source)
    assert source == {"prior_raid_count": 3, "raid_id": "R0"}
    assert derived["count_band"] == "2+"
    assert module.classify_count_band(0) == "0"
    assert module.classify_count_band(1) == "1"


def test_exp102_outputs_both_count_contrasts_census_and_all_channels(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-102")
    adapter = module.Adapter(n_boot=40, n_destroy=20, seeds=(0, 1))
    frame = adapter.fixture_frame()
    assert adapter.integrity(frame).blocking_pass
    rows = adapter.analyze(frame)
    assert {(row["arm"], row["comparator"]) for row in rows} == {
        ("1", "0"),
        ("2+", "0"),
    }
    assert {row["channel"] for row in rows} == {
        "swing_price",
        "swing_bps",
        "swing_atr",
        "swing_duration_ns",
        "strong_move",
    }
    extra = adapter.extra(frame)
    assert set(extra["census"]["count_band"]) == {"0", "1", "2+"}
    assert "censor_status" in extra["census"]
