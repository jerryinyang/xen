"""Nautilus schedule executor for the frozen SPDR-011 event population.

DEVIATIONS: none. The schedule contains census event times and directions only. A target
change is submitted by an engine-clock alert at the completed boundary. The runner sequences
the catalog's real next-bar open as an execution event one nanosecond later (L-41/L-42); no
future price enters the schedule and no emitted fill is rewritten.
"""
from __future__ import annotations

import hashlib
from decimal import Decimal

import polars as pl

from nautilus_trader.common.component import TimeEvent
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import ClientOrderId, InstrumentId
from nautilus_trader.trading.strategy import Strategy


def build_target_schedule(events: pl.DataFrame) -> pl.DataFrame:
    """Build one tagged ENTRY and EXIT action for every non-overlapping episode."""
    required = {"event_id", "symbol", "entry_ts", "exit_ts", "direction"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"events missing required columns: {missing}")
    if events.height and events["symbol"].n_unique() != 1:
        raise ValueError("build_target_schedule requires one prefiltered symbol")
    ordered = events.sort(["entry_ts", "event_id"])
    previous_exit = None
    changes: list[dict] = []
    for row in ordered.iter_rows(named=True):
        entry = row["entry_ts"]
        exit_ = row["exit_ts"]
        direction = int(row["direction"])
        if direction not in {-1, 1}:
            raise ValueError("direction must be -1 or +1")
        if exit_ <= entry:
            raise ValueError("exit_ts must be after entry_ts")
        if previous_exit is not None and entry < previous_exit:
            raise ValueError("event episodes overlap")
        changes.append(
            {
                "decision_ts": entry,
                "direction": direction,
                "symbol": row["symbol"],
                "event_id": row["event_id"],
                "action": "ENTRY",
                "client_order_id": _client_order_id(row["event_id"], "ENTRY"),
            }
        )
        changes.append(
            {
                "decision_ts": exit_,
                "direction": direction,
                "symbol": row["symbol"],
                "event_id": row["event_id"],
                "action": "EXIT",
                "client_order_id": _client_order_id(row["event_id"], "EXIT"),
            }
        )
        previous_exit = exit_

    if not changes:
        return pl.DataFrame(
            schema={
                "decision_ts": pl.Datetime("us", "UTC"),
                "direction": pl.Int8,
                "symbol": pl.Utf8,
                "event_id": pl.Utf8,
                "action": pl.Utf8,
                "client_order_id": pl.Utf8,
            }
        )
    return (
        pl.DataFrame(changes, infer_schema_length=None)
        .with_columns(
            pl.when(pl.col("action") == "EXIT").then(0).otherwise(1).alias("_priority")
        )
        .sort(["decision_ts", "_priority"])
        .with_columns(pl.col("direction").cast(pl.Int8))
        .drop("_priority")
    )


def _client_order_id(event_id: str, action: str) -> str:
    digest = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:20]
    suffix = "E" if action == "ENTRY" else "X"
    return f"S011-{digest}-{suffix}"


class Spdr011ScheduleConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    trade_size: Decimal
    schedule_path: str


class Spdr011ScheduleStrategy(Strategy):
    """Apply frozen target changes at exact engine-clock decision boundaries."""

    def __init__(self, config: Spdr011ScheduleConfig) -> None:
        super().__init__(config)
        schedule = pl.read_parquet(config.schedule_path).sort("decision_ts")
        self._timestamps = (
            schedule.select(pl.col("decision_ts").dt.epoch("ns"))["decision_ts"].to_list()
        )
        self._directions = schedule["direction"].to_list()
        self._events = schedule["event_id"].to_list()
        self._actions = schedule["action"].to_list()
        self._client_order_ids = schedule["client_order_id"].to_list()
        self._pointer = 0

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            raise RuntimeError(f"instrument not cached: {self.config.instrument_id}")
        symbol = str(self.config.instrument_id).split("-LINEAR.", maxsplit=1)[0]
        for index, decision_ts in enumerate(dict.fromkeys(self._timestamps)):
            self.clock.set_time_alert_ns(
                name=f"SPDR011-{symbol}-{index}",
                alert_time_ns=decision_ts,
                callback=self._on_decision,
            )

    def _on_decision(self, event: TimeEvent) -> None:
        while (
            self._pointer < len(self._timestamps)
            and self._timestamps[self._pointer] <= event.ts_event
        ):
            direction = int(self._directions[self._pointer])
            event_id = self._events[self._pointer]
            action = self._actions[self._pointer]
            client_order_id = self._client_order_ids[self._pointer]
            self._pointer += 1

            signed_action = direction if action == "ENTRY" else -direction
            side = OrderSide.BUY if signed_action > 0 else OrderSide.SELL
            quantity = self.instrument.make_qty(self.config.trade_size)
            order = self.order_factory.market(
                self.config.instrument_id,
                side,
                quantity,
                reduce_only=action == "EXIT",
                tags=[f"event_id={event_id}", f"action={action}"],
                client_order_id=ClientOrderId(client_order_id),
            )
            self.submit_order(order)

    def on_stop(self) -> None:
        # Fence-open unavailable episodes remain explicit/censored; no untagged close.
        pass
