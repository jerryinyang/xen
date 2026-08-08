"""Shared backtest helpers for INFR-010 Phase B smokes (synthetic data only)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.config import (
    BacktestDataConfig,
    BacktestRunConfig,
    BacktestVenueConfig,
    ImportableStrategyConfig,
    LoggingConfig,
)
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import Bar, BarType, BookOrder, OrderBookDelta
from nautilus_trader.model.enums import AccountType, BookAction, BookType, OmsType, OrderSide
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from xen.nautilus.instrument_ids import archive_symbol_to_instrument_id_str


def xrpusdt_linear_bybit():
    """Tutorial-scale Bybit linear instrument used in smokes."""
    return TestInstrumentProvider.xrpusdt_linear_bybit()


def synthetic_bars(
    instrument: Any,
    *,
    n: int = 500,
    seed: int = 42,
    start: datetime | None = None,
) -> tuple[BarType, list[Bar], pl.DataFrame]:
    """Generate deterministic synthetic 1m bars + polars bar_marks frame."""
    rng = np.random.default_rng(seed)
    t0 = start or datetime(2024, 1, 1, tzinfo=timezone.utc)
    times = pd.date_range(t0, periods=n, freq="1min", tz="UTC")
    base = 0.50 + np.cumsum(rng.normal(0.0002, 0.002, n))
    for i in range(min(100, n), min(200, n)):
        base[i] += 0.001
    for i in range(min(250, n), min(350, n)):
        base[i] -= 0.0015
    prices = np.maximum(base, 0.1)
    volumes = rng.integers(100, 1000, n)
    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")
    bars: list[Bar] = []
    rows: list[dict[str, Any]] = []
    for i in range(n):
        px = float(prices[i])
        ts = dt_to_unix_nanos(times[i].to_pydatetime())
        o, h, lo, c = px, px * 1.001, px * 0.999, px
        vol = float(volumes[i])
        bars.append(
            Bar(
                bar_type=bar_type,
                open=instrument.make_price(o),
                high=instrument.make_price(h),
                low=instrument.make_price(lo),
                close=instrument.make_price(c),
                volume=instrument.make_qty(vol),
                ts_event=ts,
                ts_init=ts,
            )
        )
        rows.append(
            {
                "SourceCloseTime": times[i].to_pydatetime().replace(tzinfo=None),
                "RealOpen": o,
                "RealHigh": h,
                "RealLow": lo,
                "RealClose": c,
                "Volume": vol,
            }
        )
    marks = pl.DataFrame(rows).with_columns(
        pl.col("SourceCloseTime").cast(pl.Datetime("ns"))
    )
    return bar_type, bars, marks


def synthetic_l2_deltas(instrument: Any, *, n_updates: int = 50) -> list[OrderBookDelta]:
    """Tutorial-scale L2_MBP delta stream (CLEAR + snapshot + imbalanced updates)."""
    deltas: list[OrderBookDelta] = []
    ts0 = 1_704_067_200_000_000_000  # 2024-01-01T00:00:00Z
    seq = 1
    deltas.append(OrderBookDelta.clear(instrument.id, seq, ts0, ts0))
    seq += 1
    levels = [
        (OrderSide.BUY, 0.5000, 500),
        (OrderSide.BUY, 0.4999, 300),
        (OrderSide.BUY, 0.4998, 200),
        (OrderSide.SELL, 0.5001, 50),
        (OrderSide.SELL, 0.5002, 40),
        (OrderSide.SELL, 0.5003, 30),
    ]
    for i, (side, px, sz) in enumerate(levels):
        ts = ts0 + i * 1_000_000
        deltas.append(
            OrderBookDelta(
                instrument_id=instrument.id,
                action=BookAction.ADD,
                order=BookOrder(
                    side=side,
                    price=instrument.make_price(px),
                    size=instrument.make_qty(sz),
                    order_id=seq,
                ),
                flags=0,
                sequence=seq,
                ts_event=ts,
                ts_init=ts,
            )
        )
        seq += 1
    for j in range(n_updates):
        ts = ts0 + 10_000_000_000 + j * 100_000_000
        deltas.append(
            OrderBookDelta(
                instrument_id=instrument.id,
                action=BookAction.UPDATE,
                order=BookOrder(
                    side=OrderSide.BUY,
                    price=instrument.make_price(0.5000),
                    size=instrument.make_qty(1000 + j * 10),
                    order_id=1,
                ),
                flags=0,
                sequence=seq,
                ts_event=ts,
                ts_init=ts,
            )
        )
        seq += 1
        deltas.append(
            OrderBookDelta(
                instrument_id=instrument.id,
                action=BookAction.UPDATE,
                order=BookOrder(
                    side=OrderSide.SELL,
                    price=instrument.make_price(0.5001),
                    size=instrument.make_qty(10),
                    order_id=4,
                ),
                flags=0,
                sequence=seq,
                ts_event=ts + 1_000_000,
                ts_init=ts + 1_000_000,
            )
        )
        seq += 1
    return deltas


def _pandas_to_polars(df: Any) -> pl.DataFrame:
    if df is None or len(df) == 0:
        return pl.DataFrame()
    # reset index so client_order_id / position_id become columns when present
    pdf = df.reset_index() if hasattr(df, "reset_index") else df
    return pl.from_pandas(pdf)


def run_ma_cross_engine(
    *,
    trade_size: str = "10",
    fast: int = 10,
    slow: int = 30,
    n_bars: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Run EMACross via BacktestEngine; return reports + bar marks + config."""
    from nautilus_trader.examples.strategies.ema_cross import EMACross, EMACrossConfig

    instrument = xrpusdt_linear_bybit()
    bar_type, bars, marks = synthetic_bars(instrument, n=n_bars, seed=seed)
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
    )
    engine = BacktestEngine(config=config)
    engine.add_venue(
        venue=Venue("BYBIT"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(100_000, USDT)],
        book_type=BookType.L1_MBP,
    )
    engine.add_instrument(instrument)
    engine.add_data(bars)
    engine.add_strategy(
        EMACross(
            EMACrossConfig(
                instrument_id=instrument.id,
                bar_type=bar_type,
                trade_size=Decimal(trade_size),
                fast_ema_period=fast,
                slow_ema_period=slow,
                request_bars=False,
            )
        )
    )
    engine.run()
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report())
    orders = _pandas_to_polars(engine.trader.generate_orders_report())
    positions = _pandas_to_polars(engine.trader.generate_positions_report())
    engine.dispose()
    run_config = {
        "strategy": "EMACross",
        "instrument_id": str(instrument.id),
        "bar_type": str(bar_type),
        "trade_size": trade_size,
        "fast_ema_period": fast,
        "slow_ema_period": slow,
        "n_bars": n_bars,
        "seed": seed,
        "venue": "BYBIT",
        "book_type": "L1_MBP",
        "oms_type": "NETTING",
        "account_type": "MARGIN",
        "starting_balances": ["100000 USDT"],
    }
    return {
        "fills": fills,
        "orders": orders,
        "positions_ledger": positions,
        "bar_marks": marks,
        "run_config": run_config,
        "instrument_id_map": {
            "XRPUSDT": archive_symbol_to_instrument_id_str("XRPUSDT"),
        },
        "instrument_id": str(instrument.id),
    }


def run_ma_cross_node(
    catalog_path: str,
    *,
    trade_size: str = "10",
    fast: int = 10,
    slow: int = 30,
    n_bars: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Write synthetic bars to a catalog and run EMACross through BacktestNode."""
    instrument = xrpusdt_linear_bybit()
    bar_type, bars, marks = synthetic_bars(instrument, n=n_bars, seed=seed)
    catalog = ParquetDataCatalog(catalog_path)
    catalog.write_data([instrument])
    catalog.write_data(bars)

    venue_config = BacktestVenueConfig(
        name="BYBIT",
        oms_type="NETTING",
        account_type="MARGIN",
        base_currency="USDT",
        starting_balances=["100000 USDT"],
        book_type="L1_MBP",
    )
    data_config = BacktestDataConfig(
        catalog_path=catalog_path,
        data_cls=Bar,
        instrument_id=str(instrument.id),
    )
    strategy_config = ImportableStrategyConfig(
        strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
        config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
        config={
            "instrument_id": str(instrument.id),
            "bar_type": str(bar_type),
            "trade_size": trade_size,
            "fast_ema_period": fast,
            "slow_ema_period": slow,
            "request_bars": False,
        },
    )
    engine_config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
        strategies=[strategy_config],
    )
    run_config = BacktestRunConfig(
        engine=engine_config,
        venues=[venue_config],
        data=[data_config],
    )
    node = BacktestNode(configs=[run_config])
    results = node.run()
    result = results[0]
    # Capture reports before dispose when engine still holds cache.
    engine = node.get_engine(run_config.id)
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report()) if engine else pl.DataFrame()
    orders = _pandas_to_polars(engine.trader.generate_orders_report()) if engine else pl.DataFrame()
    positions = (
        _pandas_to_polars(engine.trader.generate_positions_report()) if engine else pl.DataFrame()
    )
    node.dispose()
    cfg = {
        "strategy": "EMACross",
        "api": "BacktestNode",
        "instrument_id": str(instrument.id),
        "bar_type": str(bar_type),
        "trade_size": trade_size,
        "fast_ema_period": fast,
        "slow_ema_period": slow,
        "n_bars": n_bars,
        "seed": seed,
        "catalog_path": catalog_path,
        "run_config_id": run_config.id,
    }
    return {
        "fills": fills,
        "orders": orders,
        "positions_ledger": positions,
        "bar_marks": marks,
        "run_config": cfg,
        "instrument_id_map": {"XRPUSDT": archive_symbol_to_instrument_id_str("XRPUSDT")},
        "backtest_result": {
            "run_config_id": result.run_config_id,
            "iterations": result.iterations,
            "total_events": result.total_events,
            "stats_pnls": result.stats_pnls,
            "elapsed_time": result.elapsed_time,
            "backtest_start": result.backtest_start,
            "backtest_end": result.backtest_end,
        },
    }


def run_l2_mbp_engine(*, n_updates: int = 50, max_trade_size: str = "10") -> dict[str, Any]:
    """L2_MBP path smoke with OrderBookImbalance on synthetic depth."""
    from nautilus_trader.examples.strategies.orderbook_imbalance import (
        OrderBookImbalance,
        OrderBookImbalanceConfig,
    )

    instrument = xrpusdt_linear_bybit()
    deltas = synthetic_l2_deltas(instrument, n_updates=n_updates)
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
    )
    engine = BacktestEngine(config=config)
    engine.add_venue(
        venue=Venue("BYBIT"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(100_000, USDT)],
        book_type=BookType.L2_MBP,
    )
    engine.add_instrument(instrument)
    engine.add_data(deltas)
    engine.add_strategy(
        OrderBookImbalance(
            OrderBookImbalanceConfig(
                instrument_id=instrument.id,
                max_trade_size=Decimal(max_trade_size),
                trigger_min_size=100.0,
                trigger_imbalance_ratio=0.5,
                min_seconds_between_triggers=0.0,
                book_type="L2_MBP",
            )
        )
    )
    engine.run()
    book = engine.cache.order_book(instrument.id)
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report())
    orders = _pandas_to_polars(engine.trader.generate_orders_report())
    positions = _pandas_to_polars(engine.trader.generate_positions_report())
    book_summary = {
        "best_bid": str(book.best_bid_price()) if book else None,
        "best_ask": str(book.best_ask_price()) if book else None,
        "update_count": int(book.update_count) if book else 0,
        "bid_levels": book.bid_count() if book and hasattr(book, "bid_count") else None,
        "ask_levels": book.ask_count() if book and hasattr(book, "ask_count") else None,
    }
    engine.dispose()
    # Minimal bar marks so emission contract remains well-formed (one mark at stream start).
    marks = pl.DataFrame(
        {
            "SourceCloseTime": [datetime(2024, 1, 1)],
            "RealOpen": [0.5],
            "RealHigh": [0.5003],
            "RealLow": [0.4998],
            "RealClose": [0.5000],
        }
    ).with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns")))
    # Extend marks slightly so adjudication has ≥2 bars when needed.
    marks = pl.concat(
        [
            marks,
            pl.DataFrame(
                {
                    "SourceCloseTime": [datetime(2024, 1, 1, 0, 1)],
                    "RealOpen": [0.5001],
                    "RealHigh": [0.5003],
                    "RealLow": [0.4998],
                    "RealClose": [0.5001],
                }
            ).with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns"))),
        ]
    )
    return {
        "fills": fills,
        "orders": orders,
        "positions_ledger": positions,
        "bar_marks": marks,
        "book_summary": book_summary,
        "run_config": {
            "strategy": "OrderBookImbalance",
            "instrument_id": str(instrument.id),
            "book_type": "L2_MBP",
            "n_updates": n_updates,
            "max_trade_size": max_trade_size,
            "venue": "BYBIT",
        },
        "instrument_id_map": {"XRPUSDT": archive_symbol_to_instrument_id_str("XRPUSDT")},
    }
