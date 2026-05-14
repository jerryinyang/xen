from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl

from heiken_ashi_generator import HeikenAshiGenerator, generate_heiken_ashi
from linebreak_generator import LineBreakGenerator, generate_linebreak
from renko_generator import RenkoGenerator, generate_renko


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


def stream_heiken_ashi(time_bars: pl.DataFrame) -> pl.DataFrame:
    generator = HeikenAshiGenerator()
    rows = [generator.update(row) for row in time_bars.sort("CloseTime").iter_rows(named=True)]
    return pl.DataFrame(rows).select(generate_heiken_ashi(time_bars).columns)


def stream_linebreak(time_bars: pl.DataFrame, level: int) -> pl.DataFrame:
    generator = LineBreakGenerator(level=level)
    rows = []
    for row in time_bars.sort("CloseTime").iter_rows(named=True):
        rows.extend(generator.update(row))
    return pl.DataFrame(rows).select(generate_linebreak(time_bars, level=level).columns)


def stream_renko(time_bars: pl.DataFrame, atr_period: int) -> pl.DataFrame:
    generator = RenkoGenerator(atr_period=atr_period)
    rows = []
    for row in time_bars.sort("CloseTime").iter_rows(named=True):
        rows.extend(generator.update(row))
    return pl.DataFrame(rows).select(generate_renko(time_bars, atr_period=atr_period).columns)


def assert_same_frame(left: pl.DataFrame, right: pl.DataFrame) -> None:
    assert left.to_dicts() == right.to_dicts()


def test_heiken_ashi_schema_and_real_prices() -> None:
    bars = sample_bars([100.0, 101.0, 100.5])

    result = generate_heiken_ashi(bars)

    assert result.columns == [
        "OpenTime",
        "CloseTime",
        "HAOpen",
        "HAHigh",
        "HALow",
        "HAClose",
        "RealOpen",
        "RealHigh",
        "RealLow",
        "RealClose",
        "Direction",
        "SourceCount",
    ]
    assert result["RealClose"].to_list() == bars["Close"].to_list()
    assert result["SourceCount"].to_list() == [1, 1, 1]


def test_generators_are_deterministic() -> None:
    bars = sample_bars([100.0, 101.0, 102.0, 100.0, 98.0, 103.0, 106.0, 101.0])

    assert_same_frame(generate_heiken_ashi(bars), generate_heiken_ashi(bars))
    assert_same_frame(generate_linebreak(bars, level=3), generate_linebreak(bars, level=3))
    assert_same_frame(generate_renko(bars, atr_period=3), generate_renko(bars, atr_period=3))


def test_batch_matches_streaming_stateful_updates() -> None:
    bars = sample_bars([100.0, 101.0, 102.0, 100.0, 98.0, 103.0, 106.0, 101.0])

    assert_same_frame(generate_heiken_ashi(bars), stream_heiken_ashi(bars))
    assert_same_frame(generate_linebreak(bars, level=3), stream_linebreak(bars, level=3))
    assert_same_frame(generate_renko(bars, atr_period=3), stream_renko(bars, atr_period=3))


def test_generators_sort_by_close_time_before_processing() -> None:
    bars = sample_bars([100.0, 101.0, 102.0, 100.0, 98.0, 103.0])
    shuffled = bars[[2, 0, 5, 1, 4, 3]]

    assert_same_frame(generate_heiken_ashi(bars), generate_heiken_ashi(shuffled))
    assert_same_frame(generate_linebreak(bars, level=2), generate_linebreak(shuffled, level=2))
    assert_same_frame(generate_renko(bars, atr_period=3), generate_renko(shuffled, atr_period=3))


def test_linebreak_uses_level_window_for_reversal() -> None:
    bars = sample_bars([100.0, 101.0, 102.0, 101.5, 99.0])

    result = generate_linebreak(bars, level=2)

    assert result["Direction"].to_list() == [1, 1, 1, -1]
    assert result["SourceCloseTime"].to_list() == result["CloseTime"].to_list()
    assert result["Level"].to_list() == [2, 2, 2, 2]


def test_renko_waits_for_atr_window_and_uses_known_rows_only() -> None:
    bars = sample_bars([100.0, 100.1, 100.2, 102.0, 104.0])

    result = generate_renko(bars, atr_period=3)

    assert result.height > 0
    assert result["SourceCloseTime"].min() >= bars["CloseTime"][2]
    assert result["ATRPeriod"].to_list() == [3] * result.height
    assert all(size > 0 for size in result["BrickSize"].to_list())
