"""Nautilus execution of one symbol's frozen arm schedule.

Every price path runs in the engine: breakouts use native stop orders with GTD pending expiry,
while decided breach events use native market orders at their actionable next-open timestamp.
Target / protective stop / trailing stop / holding cap compete on native one-minute bars. No
local OHLC reconstruction decides which exit happened first - the engine's own event ordering
does (design section 10).

Schedule contract (one row = one arm's action on one common origin):

    arm_id, arm_class, origin_id, episode_id, decision_ts, actionable_ts, state,
    entry_order_type, side, stop_price, expiry_bars, hold_bars, target_distance_bps,
    stop_distance_bps, trail_distance_bps, trail_activation_bps, risk_size

``stop_price`` is null for a ``NO_EVENT`` row: the origin is still carried, and the strategy
records it so no origin is ever dropped.
"""

from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal
import hashlib
from pathlib import Path

import pandas as pd
import polars as pl
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, PositionId
from nautilus_trader.model.objects import Price
from nautilus_trader.trading.strategy import Strategy

from xen.adaptive_management.contracts import OriginState

SCHEDULE_COLUMNS = (
    "arm_id",
    "experiment_id",
    "native_arm_id",
    "policy_id",
    "device",
    "entry_variant",
    "exit_reason",
    "arm_class",
    "origin_id",
    "episode_id",
    "decision_ts",
    "actionable_ts",
    "state",
    "entry_order_type",
    "side",
    "stop_price",
    "expiry_bars",
    "hold_bars",
    "target_distance_bps",
    "stop_distance_bps",
    "trail_distance_bps",
    "trail_activation_bps",
    "risk_size",
)
NS_PER_HOUR = 3_600_000_000_000

# The ledger is one row per arm per state transition: millions of rows on a full TRAIN span.
# Held as a Python list it dominates worker memory, so it is flushed to disk in batches with a
# fixed schema (an inferred schema could drift between batches).
LEDGER_SCHEMA = {
    "episode_id": pl.Utf8,
    "origin_id": pl.Utf8,
    "arm_id": pl.Utf8,
    "arm_class": pl.Utf8,
    "experiment_id": pl.Utf8,
    "native_arm_id": pl.Utf8,
    "policy_id": pl.Utf8,
    "device": pl.Utf8,
    "entry_variant": pl.Utf8,
    "state": pl.Utf8,
    "ts_ns": pl.Int64,
    "price": pl.Float64,
    "exit_reason": pl.Utf8,
}
LEDGER_BATCH_ROWS = 250_000


class AdaptiveManagementConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: str
    schedule_path: str
    base_trade_size: Decimal
    fence_start_ns: int
    fence_end_ns: int
    ledger_dir: str = ""
    ledger_batch_rows: int = LEDGER_BATCH_ROWS


class AdaptiveManagementStrategy(Strategy):
    """Execute every arm on one instrument, keeping one live order or position per arm."""

    def __init__(self, config: AdaptiveManagementConfig) -> None:
        super().__init__(config)
        schedule = pl.read_parquet(config.schedule_path)
        missing = sorted(set(SCHEDULE_COLUMNS) - set(schedule.columns))
        if missing:
            raise ValueError(f"schedule missing columns: {missing}")
        schedule = schedule.with_columns(
            pl.col("decision_ts")
            .cast(pl.Datetime("ns", "UTC"))
            .dt.epoch("ns")
            .alias("_decision_ts"),
            pl.col("actionable_ts")
            .cast(pl.Datetime("ns", "UTC"))
            .dt.epoch("ns")
            .alias("_ts"),
        ).sort(["_ts", "arm_id", "episode_id"])
        outside = schedule.filter(
            (pl.col("_ts") < config.fence_start_ns)
            | (pl.col("_ts") > config.fence_end_ns)
            | (pl.col("_decision_ts") < config.fence_start_ns)
            | (pl.col("_decision_ts") > config.fence_end_ns)
        )
        if outside.height:
            raise ValueError("schedule decision timestamp outside fence")
        # A NaN distance or size would only surface as an aborted engine mid-run.
        numeric = [
            name
            for name in (
                "stop_price", "target_distance_bps", "stop_distance_bps",
                "trail_distance_bps", "trail_activation_bps", "risk_size",
            )
            if name in schedule.columns and schedule.schema[name] in (pl.Float32, pl.Float64)
        ]
        nan_columns = [
            name for name in numeric if bool(schedule[name].is_nan().fill_null(False).any())
        ]
        if nan_columns:
            raise ValueError(f"schedule contains NaN values in {nan_columns}")
        duplicate_keys = [
            "experiment_id", "arm_id", "entry_variant", "episode_id", "policy_id"
        ]
        if schedule.select(duplicate_keys).is_duplicated().any():
            raise ValueError("duplicate schedule identity")
        # One arm may act on one origin only once. Two distinct origins can share an
        # actionable timestamp (a bar qualifying on both the long and the short shape);
        # the single-slot rule resolves those at run time as BLOCKED_ACTIVE.
        overlap_keys = ["arm_id", "entry_variant", "origin_id"]
        if schedule.select(overlap_keys).is_duplicated().any():
            raise ValueError("overlapping schedule rows for one arm and entry variant")
        self._rows_by_ts: dict[int, list[dict]] = defaultdict(list)
        for row in schedule.iter_rows(named=True):
            self._rows_by_ts[int(row["_ts"])].append(row)
        self._pending_ts = deque(sorted(self._rows_by_ts))
        self._last_bar_ts: int | None = None

        # arm_id -> episode currently holding the arm's single slot
        self._busy: dict[tuple[str, str], str] = {}
        self._by_client_order: dict[str, dict] = {}
        self._entry_orders: set[str] = set()
        self._open_exits: dict[tuple[str, str], list] = defaultdict(list)
        self._hold_deadline: dict[tuple[str, str], int] = {}
        self._episode_position: dict[tuple[str, str], PositionId] = {}
        self._hold_timer: dict[tuple[str, str], str] = {}
        self._execution_rows: dict[tuple[str, str], dict] = {}
        self._orders_by_execution: dict[tuple[str, str], list[str]] = defaultdict(list)
        self._entry_terminal: set[tuple[str, str]] = set()
        self._closed: set[tuple[str, str]] = set()
        self.state_ledger: list[dict] = []
        self._ledger_parts = 0

    def flush_ledger(self) -> None:
        """Write the buffered ledger rows as the next ordered part file."""
        if not self.config.ledger_dir or not self.state_ledger:
            return
        directory = Path(self.config.ledger_dir)
        directory.mkdir(parents=True, exist_ok=True)
        frame = pl.DataFrame(self.state_ledger, schema=LEDGER_SCHEMA)
        target = directory / f"part-{self._ledger_parts:06d}.parquet"
        temporary = target.with_suffix(".parquet.tmp")
        frame.write_parquet(temporary)
        temporary.replace(target)
        self._ledger_parts += 1
        self.state_ledger.clear()

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            raise RuntimeError(f"instrument not cached: {self.config.instrument_id}")
        self.subscribe_bars(BarType.from_str(self.config.bar_type))

    def on_bar(self, bar: Bar) -> None:
        # An actionable H1 timestamp need not exist as a traded minute (a session close, a
        # holiday, a weekend). Such a row acts on the first minute at or after it, never
        # before it, so no row is stranded and nothing is pulled earlier in time.
        self._last_bar_ts = int(bar.ts_event)
        while self._pending_ts and self._pending_ts[0] <= int(bar.ts_event):
            for row in self._rows_by_ts.pop(self._pending_ts.popleft(), []):
                self._act_on_origin(row, bar)

    def on_stop(self) -> None:
        if self._rows_by_ts:
            # Rows after the final traded minute never became actionable inside the fence and
            # are censored, with their origin still recorded. Anything left at or before the
            # final bar means the run dropped a row, which stays a hard failure.
            stranded = sum(
                len(rows)
                for ts, rows in self._rows_by_ts.items()
                if self._last_bar_ts is None or ts <= self._last_bar_ts
            )
            if stranded:
                raise RuntimeError(f"{stranded} unconsumed schedule rows at stop")
            for ts in sorted(self._rows_by_ts):
                for row in self._rows_by_ts[ts]:
                    self._execution_rows[_execution_key(row)] = row
                    self._terminal_entry(row, OriginState.CENSORED, ts)
            self._rows_by_ts.clear()
            self._pending_ts.clear()
        for key, deadline in list(self._hold_deadline.items()):
            row = self._execution_rows[key]
            self._record(key[0], "OPEN_AT_FENCE_END", deadline, row)
        self.flush_ledger()

    # ------------------------------------------------------------------ #
    # origin handling
    # ------------------------------------------------------------------ #

    def _act_on_origin(self, row: dict, bar: Bar) -> None:
        """Submit the arm's entry order, or record why this origin produced no order."""
        episode_id = str(row["episode_id"])
        arm_id = str(row["arm_id"])
        slot = (arm_id, str(row["entry_variant"]))
        key = _execution_key(row)
        self._execution_rows[key] = row
        state = str(row["state"])
        entry_order_type = str(row["entry_order_type"])
        if state != str(OriginState.ORDER_CREATED):
            self._terminal_entry(row, state, bar.ts_event)
            return
        if slot in self._busy:
            self._terminal_entry(row, OriginState.BLOCKED_ACTIVE, bar.ts_event)
            return

        side = OrderSide.BUY if int(row["side"]) > 0 else OrderSide.SELL
        quantity = self.instrument.make_qty(
            self.config.base_trade_size * Decimal(str(row["risk_size"] or 1.0))
        )
        tags = [
            *_identity_tags(row),
            "device=NONE",
            "exit_reason=NULL",
            "leg=ENTRY",
        ]
        if entry_order_type == "STOP":
            if row["stop_price"] is None or row["expiry_bars"] is None:
                raise ValueError("STOP entry requires stop_price and expiry_bars")
            expire_ns = int(bar.ts_event) + int(row["expiry_bars"]) * NS_PER_HOUR
            order = self.order_factory.stop_market(
                instrument_id=self.config.instrument_id,
                order_side=side,
                quantity=quantity,
                trigger_price=self.instrument.make_price(float(row["stop_price"])),
                time_in_force=TimeInForce.GTD,
                expire_time=pd.Timestamp(expire_ns, tz="UTC"),
                tags=tags,
            )
        elif entry_order_type == "MARKET":
            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=side,
                quantity=quantity,
                tags=tags,
            )
        else:
            raise ValueError(f"ORDER_CREATED row has invalid entry_order_type={entry_order_type}")
        self._busy[slot] = episode_id
        self._by_client_order[str(order.client_order_id)] = row
        self._orders_by_execution[_execution_key(row)].append(str(order.client_order_id))
        self._entry_orders.add(str(order.client_order_id))
        self._record(episode_id, OriginState.ORDER_CREATED, bar.ts_event, row)
        self.submit_order(order, position_id=_position_id(row))

    # ------------------------------------------------------------------ #
    # order events
    # ------------------------------------------------------------------ #

    def on_order_filled(self, event) -> None:
        row = self._by_client_order.get(str(event.client_order_id))
        if row is None:
            return
        order = self.cache.order(event.client_order_id)
        if str(event.client_order_id) in self._entry_orders:
            self._on_entry_filled(row, event)
        else:
            self._on_exit_filled(row, event, order)

    def on_order_expired(self, event) -> None:
        row = self._by_client_order.get(str(event.client_order_id))
        if row is None:
            return
        if str(event.client_order_id) in self._entry_orders:
            self._terminal_entry(row, OriginState.EXPIRED, event.ts_event)
            self._release(row, None, event.ts_event)

    def on_order_canceled(self, event) -> None:
        row = self._by_client_order.get(str(event.client_order_id))
        if row is not None and str(event.client_order_id) in self._entry_orders:
            self._terminal_entry(row, OriginState.EXPIRED, event.ts_event)
            self._release(row, None, event.ts_event)

    def on_order_rejected(self, event) -> None:
        self._handle_order_failure(event, OriginState.REJECTED)

    def on_order_denied(self, event) -> None:
        self._handle_order_failure(event, OriginState.DENIED)

    def _handle_order_failure(self, event, state: OriginState) -> None:
        row = self._by_client_order.get(str(event.client_order_id))
        if row is None:
            return
        if str(event.client_order_id) in self._entry_orders:
            self._terminal_entry(row, state, event.ts_event)
            self._release(row, None, event.ts_event)
        else:
            # A combination arm submits several exit legs, and each leg can fail on its own.
            # Name the failing leg so its ledger row is distinguishable from its siblings.
            order = self.cache.order(event.client_order_id)
            leg = _tag_value(order, "device") if order is not None else None
            self._record(
                str(row["episode_id"]),
                f"EXIT_{state}",
                event.ts_event,
                row,
                exit_reason=leg,
            )

    def _on_entry_filled(self, row: dict, event) -> None:
        key = _execution_key(row)
        entry_price = float(event.last_px)
        side = int(row["side"])
        if key in self._episode_position:
            # A venue may fill one entry order in several slices. The episode already has its
            # terminal FILLED row, its position and its hold timer; only the incremental
            # quantity still needs exits, so the exit legs stay matched to the exposure.
            exit_side = OrderSide.SELL if side > 0 else OrderSide.BUY
            for device, distance in (
                ("TARGET", row["target_distance_bps"]),
                ("STOP", row["stop_distance_bps"]),
                ("TRAIL", row["trail_distance_bps"]),
            ):
                if distance is None:
                    continue
                self._submit_exit(
                    row, device, float(distance), entry_price, exit_side, event.last_qty
                )
            return
        self._terminal_entry(row, OriginState.FILLED, event.ts_event, price=entry_price)
        self._episode_position[key] = _position_id(row)
        if row["hold_bars"] is not None:
            deadline = int(event.ts_event) + int(
                row["hold_bars"]
            ) * NS_PER_HOUR
            self._hold_deadline[key] = deadline
            timer_name = f"hold-{_position_id(row)}"
            self._hold_timer[key] = timer_name
            self.clock.set_time_alert(
                timer_name,
                pd.Timestamp(deadline, tz="UTC"),
                callback=self._on_hold_timer,
            )
        exit_side = OrderSide.SELL if side > 0 else OrderSide.BUY
        quantity = event.last_qty

        for device, distance in (
            ("TARGET", row["target_distance_bps"]),
            ("STOP", row["stop_distance_bps"]),
            ("TRAIL", row["trail_distance_bps"]),
        ):
            if distance is None:
                continue
            self._submit_exit(row, device, float(distance), entry_price, exit_side, quantity)

    def _submit_exit(
        self,
        row: dict,
        device: str,
        distance_bps: float,
        entry_price: float,
        exit_side: OrderSide,
        quantity,
    ) -> None:
        side = int(row["side"])
        offset = entry_price * distance_bps / 1e4
        tags = [
            *_identity_tags(row),
            f"device={device}",
            f"exit_reason={device}",
            f"leg={device}",
        ]
        if device == "TARGET":
            price = entry_price + side * offset
            order = self.order_factory.limit(
                instrument_id=self.config.instrument_id,
                order_side=exit_side,
                quantity=quantity,
                price=self.instrument.make_price(price),
                reduce_only=True,
                tags=tags,
            )
        elif device == "STOP":
            price = entry_price - side * offset
            order = self.order_factory.stop_market(
                instrument_id=self.config.instrument_id,
                order_side=exit_side,
                quantity=quantity,
                trigger_price=self.instrument.make_price(price),
                reduce_only=True,
                tags=tags,
            )
        else:
            activation = entry_price + side * float(row["trail_activation_bps"] or 0.0) * (
                entry_price / 1e4
            )
            order = self.order_factory.trailing_stop_market(
                instrument_id=self.config.instrument_id,
                order_side=exit_side,
                quantity=quantity,
                trailing_offset=Decimal(str(round(offset, 8))),
                activation_price=self.instrument.make_price(activation),
                reduce_only=True,
                tags=tags,
            )
        self._by_client_order[str(order.client_order_id)] = row
        self._orders_by_execution[_execution_key(row)].append(str(order.client_order_id))
        key = _execution_key(row)
        self._open_exits[key].append(order)
        self.submit_order(order, position_id=self._episode_position[key])

    def _on_exit_filled(self, row: dict, event, order=None) -> None:
        episode_id = str(row["episode_id"])
        key = _execution_key(row)
        if key in self._closed:
            return
        self._closed.add(key)
        self._record(
            episode_id,
            "CLOSED",
            event.ts_event,
            row,
            price=float(event.last_px),
            exit_reason=_tag_value(order, "device") or "HOLD",
        )
        self._cancel_siblings(key, exclude=str(event.client_order_id))
        self._hold_deadline.pop(key, None)
        timer_name = self._hold_timer.pop(key, None)
        if timer_name is not None and timer_name in self.clock.timer_names:
            self.clock.cancel_timer(timer_name)
        self._release(row, None, event.ts_event)
        self._episode_position.pop(key, None)
        self._open_exits.pop(key, None)
        self._forget(key)

    # ------------------------------------------------------------------ #
    # holding cap + bookkeeping
    # ------------------------------------------------------------------ #

    def _on_hold_timer(self, event) -> None:
        key = next(
            (execution for execution, name in self._hold_timer.items() if name == event.name),
            None,
        )
        if key is None:
            return
        row = self._execution_rows[key]
        self._record(key[0], "HOLD_DUE", event.ts_event, row)
        position_id = self._episode_position.get(key)
        position = self.cache.position(position_id) if position_id else None
        self._hold_deadline.pop(key, None)
        if position is None or position.is_closed:
            return
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL if position.is_long else OrderSide.BUY,
            quantity=position.quantity,
            reduce_only=True,
            tags=[*_identity_tags(row), "device=HOLD", "exit_reason=HOLD", "leg=HOLD"],
        )
        self._by_client_order[str(order.client_order_id)] = row
        self._orders_by_execution[_execution_key(row)].append(str(order.client_order_id))
        self.submit_order(order, position_id=position_id)

    def _cancel_siblings(self, key: tuple[str, str], exclude: str) -> None:
        for order in self._open_exits.pop(key, []):
            if str(order.client_order_id) == exclude:
                continue
            if order.is_open:
                self.cancel_order(order)

    def _release(self, row: dict, state: str | None, ts: int) -> None:
        slot = (str(row["arm_id"]), str(row["entry_variant"]))
        if self._busy.get(slot) == str(row["episode_id"]):
            del self._busy[slot]
        if state is not None:
            self._record(str(row["episode_id"]), state, ts, row)

    def _terminal_entry(
        self,
        row: dict,
        state: str,
        ts: int,
        *,
        price: float | None = None,
    ) -> None:
        episode_id = str(row["episode_id"])
        key = _execution_key(row)
        if key in self._entry_terminal:
            return
        self._entry_terminal.add(key)
        self._record(episode_id, state, ts, row, price=price)
        if state != str(OriginState.FILLED):
            # The episode never opened, so nothing later reads its row. A symbol carries
            # millions of schedule rows; retaining every one is what made engine memory grow
            # without bound through the run.
            self._forget(key)

    def _forget(self, key: tuple[str, str]) -> None:
        """Release per-episode state that no later event or stop-time record can reach."""
        if key in self._hold_deadline:
            return
        self._execution_rows.pop(key, None)
        for client_order_id in self._orders_by_execution.pop(key, ()):  # noqa: B007
            self._by_client_order.pop(client_order_id, None)

    def _record(
        self,
        episode_id: str,
        state: str,
        ts: int,
        row: dict | None = None,
        price: float | None = None,
        exit_reason: str | None = None,
    ) -> None:
        self.state_ledger.append(
            {
                "episode_id": episode_id,
                "origin_id": str(row["origin_id"]) if row else None,
                "arm_id": str(row["arm_id"]) if row else None,
                "arm_class": str(row["arm_class"]) if row else None,
                "experiment_id": str(row["experiment_id"]) if row else None,
                "native_arm_id": str(row["native_arm_id"]) if row else None,
                "policy_id": str(row["policy_id"]) if row else None,
                "device": str(row["device"]) if row else None,
                "entry_variant": str(row["entry_variant"]) if row else None,
                "state": str(state),
                "ts_ns": int(ts),
                "price": price,
                "exit_reason": exit_reason,
            }
        )
        if (
            self.config.ledger_dir
            and len(self.state_ledger) >= self.config.ledger_batch_rows
        ):
            self.flush_ledger()


def _tag_value(order_or_event, key: str) -> str | None:
    """Read a `key=value` tag. Order events carry no tags, so callers pass the order."""
    tags = getattr(order_or_event, "tags", None)
    if not tags:
        return None
    for tag in tags:
        if tag.startswith(f"{key}="):
            return tag.split("=", 1)[1]
    return None


def _identity_tags(row: dict) -> list[str]:
    return [
        f"experiment_id={row['experiment_id']}",
        f"arm_id={row['arm_id']}",
        f"arm_class={row['arm_class']}",
        f"native_arm_id={row['native_arm_id']}",
        f"policy_id={row['policy_id']}",
        f"episode_id={row['episode_id']}",
        f"origin_id={row['origin_id']}",
        f"entry_variant={row['entry_variant']}",
    ]


def _position_id(row: dict) -> PositionId:
    material = "|".join(
        str(row[key])
        for key in (
            "experiment_id", "arm_id", "entry_variant", "episode_id", "policy_id"
        )
    )
    return PositionId(f"AM-{hashlib.sha256(material.encode()).hexdigest()[:32]}")


def _execution_key(row: dict) -> tuple[str, str]:
    return str(row["episode_id"]), str(row["policy_id"])


def make_price(instrument, value: float) -> Price:
    """Round a raw price to the instrument's tick size."""
    return instrument.make_price(value)
