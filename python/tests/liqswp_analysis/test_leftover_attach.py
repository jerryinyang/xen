from __future__ import annotations

import polars as pl

from xen.liqswp_analysis.leftover import attach_shared_leftover


def test_non_primary_keeps_own_first_push_and_inherits_the_set_leftover() -> None:
    frame = pl.DataFrame(
        {
            "source_cell": ["a", "a", "a"],
            "side": ["HIGH", "HIGH", "HIGH"],
            "raid_id": ["p", "n1", "n2"],
            "status": ["COMPLETED", "CONFIRMED_NON_PRIMARY", "CONFIRMED_NON_PRIMARY"],
            "primary_attribution": [True, False, False],
            "primary_completed": [True, False, False],
            "confirmation_ts_ns": [100, None, None],
            "endpoint_ts_ns": [400, 100, 100],
            "confirmation_method": ["BREAKOUT_BAR", None, None],
            "confirmation_reference": ["1H", None, None],
            "max_excursion_atr": [1.0, 2.0, 0.4],
            "swing_atr": [1.5, None, None],
            "swing_duration_ns": [10, None, None],
            "duration_ns": [10, None, None],
            "strong_move": [True, None, None],
            "swing_price": [2.0, None, None],
            "swing_bps": [20.0, None, None],
        }
    )
    result = attach_shared_leftover(frame).sort("raid_id")
    n1 = result.filter(pl.col("raid_id") == "n1").row(0, named=True)
    n2 = result.filter(pl.col("raid_id") == "n2").row(0, named=True)
    assert n1["max_excursion_atr"] == 2.0
    assert n1["swing_atr"] == 1.5
    assert n1["strong_move"] is False
    assert n1["confirmation_method"] == "BREAKOUT_BAR"
    assert n1["confirmation_ts_ns"] == 100
    assert n1["endpoint_ts_ns"] == 400
    assert n2["strong_move"] is True
    assert n2["swing_duration_ns"] == 10


def test_exp101_channel_frame_keeps_attached_non_primaries(
    load_exp_module,
) -> None:
    module = load_exp_module("EXP-101")
    adapter = module.Adapter(n_boot=2, n_destroy=2, seeds=(0,))
    frame = pl.DataFrame(
        {
            "source_cell": ["a", "a"],
            "side": ["HIGH", "HIGH"],
            "raid_id": ["p", "n1"],
            "status": ["COMPLETED", "CONFIRMED_NON_PRIMARY"],
            "primary_attribution": [True, False],
            "primary_completed": [True, False],
            "confirmation_ts_ns": [100, None],
            "endpoint_ts_ns": [400, 100],
            "confirmation_method": ["BREAKOUT_BAR", None],
            "confirmation_reference": ["1H", None],
            "max_excursion_atr": [1.0, 2.0],
            "swing_atr": [1.5, None],
            "swing_duration_ns": [10, None],
            "duration_ns": [10, None],
            "strong_move": [True, None],
            "profile_undefined_reason": [None, None],
        }
    )
    prepared = adapter.prepare_frame(frame)
    channel = adapter._channel_frame(prepared, "strong_move")
    assert channel.height == 2
    assert set(channel["raid_id"].to_list()) == {"p", "n1"}


def test_fixture_completed_rows_pass_through_without_source_cell() -> None:
    frame = pl.DataFrame(
        {
            "status": ["COMPLETED"],
            "primary_attribution": [True],
            "primary_completed": [True],
            "swing_atr": [1.0],
            "strong_move": [True],
        }
    )
    assert attach_shared_leftover(frame).height == 1
    assert attach_shared_leftover(frame)["swing_atr"][0] == 1.0
