"""Frozen ordered SPDR-011 layer inputs.

This module only exposes predeclared populations and columns. Statistical interrogation
belongs to the data-analysis stage and must consume these views in L1 -> L5 order.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any

import polars as pl


class LayerInput:
    """One immutable layer population plus an estimand description."""

    def __init__(self, frame: pl.DataFrame, metadata: dict[str, Any]) -> None:
        self.frame = frame
        self.metadata = metadata


def ordered_layer_inputs(artifact: pl.DataFrame) -> OrderedDict[str, LayerInput]:
    """Return all five predeclared views without selecting or dropping an arm by value."""
    complete = artifact.filter(pl.col("4h_available"))
    high = complete.filter(pl.col("vol_tercile") == "HIGH")
    top2 = high.filter(pl.col("top2"))
    return OrderedDict(
        (
            (
                "L1",
                LayerInput(
                    high,
                    {
                        "estimand": "HIGH 4h signed gross minus fees/funding/2bps allowance",
                        "allowance_arms_bps": [0, 2, 5],
                    },
                ),
            ),
            (
                "L2",
                LayerInput(
                    complete,
                    {
                        "estimand": "HIGH minus MID/LOW 4h absolute open-to-open move",
                        "timing_horizons_hours": [1, 2, 4],
                    },
                ),
            ),
            (
                "L3",
                LayerInput(
                    complete,
                    {
                        "estimand": "HIGH minus MID/LOW signed 4h partial residue",
                        "controls": ["unconditional_breakout", "direction_derangement"],
                    },
                ),
            ),
            (
                "L4",
                LayerInput(
                    high,
                    {
                        "estimand": "TOP2 minus occupancy/beta-matched random top-2",
                        "rank_arms": [1, 2, 3],
                    },
                ),
            ),
            (
                "L5",
                LayerInput(
                    top2,
                    {
                        "estimand": "upper-tercile aligned flow minus remainder",
                        "mirror": "reversed_sign",
                    },
                ),
            ),
        )
    )
