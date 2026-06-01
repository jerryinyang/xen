from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl
import pytest

from xen.bar_aggregator import aggregate_ohlc


def sample_bars(closes: list[float]) -> pl.DataFrame:
    start = datetime(2026, 1, 1, 0, 0)
    rows = []
    previous = closes[0]
    for index, close in enumerate(closes):
        open_price = previous if index else close
        high = max(open_price, close) + 0.2
        low = min(open_price, close) - 0.2
        rows.append(
            {
                "Symbol": "EURUSD",
                "OpenTime": start + timedelta(minutes=index),
                "CloseTime": start + timedelta(minutes=index + 1),
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": close,
                "TickVolume": 100 + index,
            }
        )
        previous = close
    return pl.DataFrame(rows)


def test_aggregate_ohlc_pairs_consecutive_bars() -> None:
    # Six 1-minute bars at minutes 1..6 fall into three clock-aligned 2-minute
    # windows: (bar0,bar1), (bar2,bar3), (bar4,bar5).
    bars = sample_bars([100.0, 101.0, 102.0, 100.0, 98.0, 103.0])

    result = aggregate_ohlc(bars, period_minutes=2)

    assert result.height == 3
    assert result["SourceBars"].to_list() == [2, 2, 2]
    for out_idx, src in enumerate(range(0, bars.height, 2)):
        pair = bars[src : src + 2]
        row = result[out_idx]
        # Open = first bar's open, Close = last bar's close (within-group order
        # must follow CloseTime — this guards against the removed internal sort).
        assert row["Open"][0] == pair["Open"][0]
        assert row["Close"][0] == pair["Close"][1]
        assert row["High"][0] == pair["High"].max()
        assert row["Low"][0] == pair["Low"].min()
        assert row["TickVolume"][0] == int(pair["TickVolume"].sum())
        assert row["CloseTime"][0] == pair["CloseTime"][1]


def test_aggregate_ohlc_rejects_unsorted_input() -> None:
    bars = sample_bars([100.0, 101.0, 102.0, 100.0, 98.0, 103.0])
    shuffled = bars[[2, 0, 5, 1, 4, 3]]

    with pytest.raises(ValueError, match="sorted by CloseTime"):
        aggregate_ohlc(shuffled, period_minutes=2)
