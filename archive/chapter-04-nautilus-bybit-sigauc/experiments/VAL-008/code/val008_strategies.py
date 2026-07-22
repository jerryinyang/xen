"""VAL-008 Nautilus strategies — MACrossFlip (in-engine causal) + ScheduleExecutor.

DEVIATIONS: none. Implements design.md §4/§5 exactly:
- MACrossFlip: SMA(20/100) on 1m closes, signal on the CONFIRMED bar close t (own deque,
  data <= t only), always-in flip via MARKET order (fills at bar t+1 open in bar execution).
- ScheduleExecutor: target-position sequence precomputed by gen_schedules.py (LEAK / LEAK-SHUF
  / LEAK-LAG1 / BASELINE-SHUF arms); applies target changes on the scheduled decision-bar
  close, so fills also land at the next bar open. No price logic in-strategy.
"""
from __future__ import annotations

from collections import deque
from decimal import Decimal

import polars as pl

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy


class MACrossFlipConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    fast_period: int = 20
    slow_period: int = 100


class MACrossFlip(Strategy):
    """SMA cross, always-in flip. Decision on confirmed bar close; fill at next bar open."""

    def __init__(self, config: MACrossFlipConfig) -> None:
        super().__init__(config)
        self._closes: deque[float] = deque(maxlen=config.slow_period)
        self._sum_fast = 0.0
        self._sum_slow = 0.0
        self._sig = 0  # current target direction (+1/-1; 0 = warmup)

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        closes = self._closes
        closes.append(float(bar.close))
        if len(closes) < self.config.slow_period:
            return
        n_fast = self.config.fast_period
        vals = list(closes)
        fast = sum(vals[-n_fast:]) / n_fast
        slow = sum(vals) / len(vals)
        sig = 1 if fast > slow else -1
        if sig == self._sig:
            return
        delta = sig - self._sig  # +2/-2 on flip, +1/-1 on first signal
        self._sig = sig
        qty = self.instrument.make_qty(self.config.trade_size * abs(delta))
        side = OrderSide.BUY if delta > 0 else OrderSide.SELL
        self.submit_order(self.order_factory.market(self.config.instrument_id, side, qty))

    def on_stop(self) -> None:
        self.close_all_positions(self.config.instrument_id)


class ScheduleExecutorConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    schedule_path: str  # parquet: ts_ns (int64, decision-bar ts_event), target (int8)


class ScheduleExecutor(Strategy):
    """Applies a precomputed target-position sequence on scheduled decision-bar closes."""

    def __init__(self, config: ScheduleExecutorConfig) -> None:
        super().__init__(config)
        sched = pl.read_parquet(config.schedule_path).sort("ts_ns")
        self._ts = sched.get_column("ts_ns").to_list()
        self._targets = sched.get_column("target").to_list()
        self._ptr = 0
        self._state = 0  # intended target position in units of trade_size

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        target = None
        while self._ptr < len(self._ts) and self._ts[self._ptr] <= bar.ts_event:
            target = self._targets[self._ptr]
            self._ptr += 1
        if target is None or target == self._state:
            return
        delta = target - self._state
        self._state = target
        qty = self.instrument.make_qty(self.config.trade_size * abs(delta))
        side = OrderSide.BUY if delta > 0 else OrderSide.SELL
        self.submit_order(self.order_factory.market(self.config.instrument_id, side, qty))

    def on_stop(self) -> None:
        self.close_all_positions(self.config.instrument_id)
