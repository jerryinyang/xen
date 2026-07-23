"""SPDR-011 immutable event-artifact assembly helpers.

DEVIATIONS: none.

This module does not locate signals or run a vectorized strategy. It joins the frozen
census membership to marks emitted by Nautilus and to attested ``SignedBar`` aggregates.
All outcome reads are at the entry timestamp or later; all conditioning timestamps must
be known no later than the trigger timestamp. Missing future marks remain explicit nulls.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

import polars as pl

from xen.evaluation import bybit_round_trip_cost_bps


FUNDING_HOURS = (0, 8, 16)
ALLOWANCE_BPS = (0.0, 2.0, 5.0)


def stable_payload_hash(payload: dict[str, Any]) -> str:
    """Return a deterministic SHA-256 for a frozen JSON-compatible payload."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _required(frame: pl.DataFrame, names: set[str], label: str) -> None:
    missing = sorted(names - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _mark_at(marks: pl.DataFrame, suffix: str, hours: int) -> pl.DataFrame:
    return marks.select(
        "symbol",
        (
            pl.col("SourceCloseTime")
            - pl.duration(minutes=1)
            - pl.duration(hours=hours)
        ).alias("entry_ts"),
        pl.col("RealOpen").alias(f"open_{suffix}"),
    )


def attach_open_to_open_outcomes(
    events: pl.DataFrame,
    bar_marks: pl.DataFrame,
) -> pl.DataFrame:
    """Attach 1h/2h/4h real-open outcomes without changing located membership.

    Timestamp provenance: entry open reads ``RealOpen`` at ``entry_ts``; horizon opens
    read ``RealOpen`` at ``entry_ts + horizon``. No price contributes to eligibility.
    """
    _required(
        events,
        {"event_id", "symbol", "entry_ts", "direction"},
        "events",
    )
    _required(bar_marks, {"symbol", "SourceCloseTime", "RealOpen"}, "bar_marks")
    if events["event_id"].n_unique() != events.height:
        raise ValueError("event_id must be unique")
    if bar_marks.select("symbol", "SourceCloseTime").n_unique() != bar_marks.height:
        raise ValueError("bar marks must be unique by symbol and SourceCloseTime")

    marks = bar_marks.select("symbol", "SourceCloseTime", "RealOpen")
    out = events.join(
        marks.select(
            "symbol",
            (pl.col("SourceCloseTime") - pl.duration(minutes=1)).alias("entry_ts"),
            pl.col("RealOpen").alias("entry_open"),
        ),
        on=["symbol", "entry_ts"],
        how="left",
        validate="m:1",
    )
    for suffix, hours in (("1h", 1), ("2h", 2), ("4h", 4)):
        out = out.join(
            _mark_at(marks, suffix, hours),
            on=["symbol", "entry_ts"],
            how="left",
            validate="m:1",
        ).with_columns(
            pl.col("entry_open").is_not_null().and_(pl.col(f"open_{suffix}").is_not_null())
            .alias(f"{suffix}_available"),
            pl.when(
                pl.col("entry_open").is_not_null()
                & pl.col(f"open_{suffix}").is_not_null()
                & (pl.col("entry_open") > 0)
            )
            .then(
                pl.col("direction")
                * (pl.col(f"open_{suffix}") / pl.col("entry_open") - 1.0)
                * 10_000.0
            )
            .otherwise(None)
            .alias(f"gross_signed_{suffix}_bps"),
            pl.when(
                pl.col("entry_open").is_not_null()
                & pl.col(f"open_{suffix}").is_not_null()
                & (pl.col("entry_open") > 0)
            )
            .then(
                ((pl.col(f"open_{suffix}") / pl.col("entry_open") - 1.0) * 10_000.0).abs()
            )
            .otherwise(None)
            .alias(f"gross_absolute_{suffix}_bps"),
        )

    return out.with_columns(
        pl.when(pl.col("entry_open").is_null())
        .then(pl.lit("ENTRY_MARK_MISSING"))
        .when(pl.col("open_4h").is_null())
        .then(pl.lit("EXIT_4H_MARK_MISSING"))
        .otherwise(pl.lit(None, dtype=pl.Utf8))
        .alias("outcome_unavailable_reason"),
        pl.lit(True).alias("located"),
    ).sort("event_id")


def funding_stamp_count(entry: datetime, exit_: datetime) -> int:
    """Public discrete funding count in ``(entry, exit]``."""
    from datetime import timedelta

    if exit_ <= entry:
        raise ValueError("exit_ts must be after entry_ts")
    cursor = entry.replace(hour=0, minute=0, second=0, microsecond=0)
    count = 0
    while cursor <= exit_:
        if cursor > entry and cursor.hour in FUNDING_HOURS:
            count += 1
        cursor += timedelta(hours=8)
    return count


def attach_partial_costs(outcomes: pl.DataFrame) -> pl.DataFrame:
    """Attach shared Bybit fee/funding cost and fixed 0/2/5-bps allowances.

    Spread is deliberately passed as ``None`` and remains null/unavailable. Outcome rows
    without a complete 4h mark retain cost metadata but have null partial-net values.
    """
    _required(
        outcomes,
        {"event_id", "entry_ts", "exit_ts", "entry_open", "gross_signed_4h_bps", "4h_available"},
        "outcomes",
    )
    rows: list[dict[str, Any]] = []
    for entry, exit_, price in outcomes.select("entry_ts", "exit_ts", "entry_open").iter_rows():
        stamps = funding_stamp_count(entry, exit_)
        cost = bybit_round_trip_cost_bps(
            "USDT_PERP",
            float(price) if price is not None else 1.0,
            liquidity="taker",
            spread_bps=None,
            funding_bps_per_8h=1.0,
            funding_stamps=stamps,
            funding_coverage="OK",
        )
        rows.append({"funding_stamps": stamps, **cost})
    costs = pl.DataFrame(rows, infer_schema_length=None)
    out = outcomes.with_row_index("_row").hstack(costs.with_row_index("_row").drop("_row"))
    exprs = []
    for allowance in ALLOWANCE_BPS:
        label = str(int(allowance))
        exprs.append(
            pl.when(pl.col("4h_available"))
            .then(pl.col("gross_signed_4h_bps") - pl.col("total_bps") - allowance)
            .otherwise(None)
            .alias(f"partial_net_{label}bps")
        )
    return out.with_columns(exprs).drop("_row")


def attach_signed_flow(events: pl.DataFrame, signed_slots: pl.DataFrame) -> pl.DataFrame:
    """Join attested completed-slot signed flow known no later than the trigger."""
    _required(events, {"symbol", "trigger_ts", "direction"}, "events")
    _required(
        signed_slots,
        {
            "symbol",
            "trigger_ts",
            "signed_known_ts",
            "BuyVolume",
            "SellVolume",
            "Volume",
            "flow_pct_long",
            "flow_pct_short",
        },
        "signed_slots",
    )
    volume_scale = pl.max_horizontal(pl.col("Volume").abs(), pl.lit(1.0))
    volume_error = signed_slots.filter(
        (pl.col("BuyVolume") + pl.col("SellVolume") - pl.col("Volume")).abs()
        > 1e-9 * volume_scale
    )
    if volume_error.height:
        raise ValueError("BuyVolume + SellVolume must equal Volume")
    joined = events.join(
        signed_slots,
        on=["symbol", "trigger_ts"],
        how="left",
        validate="m:1",
    )
    late = joined.filter(
        pl.col("signed_known_ts").is_not_null()
        & (pl.col("signed_known_ts") > pl.col("trigger_ts"))
    )
    if late.height:
        raise ValueError("signed flow known after trigger")
    total = pl.col("BuyVolume") + pl.col("SellVolume")
    return joined.with_columns(
        pl.when(total > 0)
        .then((pl.col("BuyVolume") - pl.col("SellVolume")) / total)
        .otherwise(None)
        .alias("imbalance"),
    ).with_columns(
        (pl.col("direction") * pl.col("imbalance")).alias("aligned_flow"),
        pl.when(pl.col("direction") == 1)
        .then(pl.col("flow_pct_long"))
        .otherwise(pl.col("flow_pct_short"))
        .alias("flow_pct"),
    ).with_columns(
        (pl.col("flow_pct") >= (2.0 / 3.0)).fill_null(False).alias("flow_upper_tercile"),
    )


def _side_name(value: Any) -> str:
    return str(value).upper().split(".")[-1]


def reconcile_event_fills(
    events: pl.DataFrame,
    schedule: pl.DataFrame,
    fills: pl.DataFrame,
    orders: pl.DataFrame,
    bar_marks: pl.DataFrame,
    *,
    relative_price_tolerance: float = 1e-9,
    execution_offset_ns_by_symbol: dict[str, int] | None = None,
) -> dict[str, pl.DataFrame]:
    """Reconcile every tagged event action to one Nautilus order/fill and first-minute open."""
    _required(
        events,
        {
            "event_id",
            "symbol",
            "direction",
            "4h_available",
            "outcome_unavailable_reason",
        },
        "events",
    )
    _required(
        schedule,
        {"event_id", "decision_ts", "direction", "action", "client_order_id"},
        "schedule",
    )
    _required(
        fills,
        {"client_order_id", "instrument_id", "side", "avg_px", "ts_last"},
        "fills",
    )
    _required(orders, {"client_order_id", "status"}, "orders")
    _required(bar_marks, {"symbol", "SourceCloseTime", "RealOpen"}, "bar_marks")
    if schedule["client_order_id"].n_unique() != schedule.height:
        raise RuntimeError("fill reconciliation: schedule client_order_id is not unique")

    event_rows = {row["event_id"]: row for row in events.iter_rows(named=True)}
    if len(event_rows) != events.height:
        raise RuntimeError("fill reconciliation: event_id is not unique")
    schedule_rows = schedule.with_columns(
        pl.col("decision_ts").dt.epoch("ns").alias("_decision_ts_ns")
    )
    fill_ts_expr = (
        pl.col("ts_last").dt.epoch("ns")
        if isinstance(fills.schema["ts_last"], pl.Datetime)
        else pl.col("ts_last").cast(pl.Int64)
    )
    fill_rows: dict[str, list[dict[str, Any]]] = {}
    for row in fills.with_columns(fill_ts_expr.alias("_ts_last_ns")).iter_rows(
        named=True
    ):
        fill_rows.setdefault(str(row["client_order_id"]), []).append(row)
    order_rows: dict[str, list[dict[str, Any]]] = {}
    for row in orders.iter_rows(named=True):
        order_rows.setdefault(str(row["client_order_id"]), []).append(row)
    mark_rows = {
        (row["symbol"], row["SourceCloseTime"]): row
        for row in bar_marks.iter_rows(named=True)
    }

    action_records: list[dict[str, Any]] = []
    errors: list[str] = []
    execution_offsets = execution_offset_ns_by_symbol or {}
    expected_clients = set(schedule["client_order_id"].to_list())
    unknown_fills = sorted(set(fill_rows) - expected_clients)
    unknown_orders = sorted(set(order_rows) - expected_clients)
    if unknown_fills or unknown_orders:
        errors.append(
            f"unknown tagged activity fills={unknown_fills[:3]} orders={unknown_orders[:3]}"
        )
    for event_id in event_rows:
        actions = schedule_rows.filter(pl.col("event_id") == event_id)["action"].to_list()
        if event_rows[event_id]["4h_available"] and sorted(actions) != ["ENTRY", "EXIT"]:
            errors.append(f"{event_id}: expected exactly one ENTRY and one EXIT schedule action")
    for expected in schedule_rows.iter_rows(named=True):
        event = event_rows[expected["event_id"]]
        client_id = expected["client_order_id"]
        action = expected["action"]
        complete = bool(event["4h_available"])
        expected_fill_ns = (
            expected["_decision_ts_ns"] + execution_offsets.get(event["symbol"], 0) + 2
        )
        expected_source_ts = expected["decision_ts"] + timedelta(minutes=1)
        mark = mark_rows.get((event["symbol"], expected_source_ts))
        action_fills = fill_rows.get(client_id, [])
        action_orders = order_rows.get(client_id, [])
        order_count = len(action_orders)
        expected_side = (
            "BUY"
            if (expected["direction"] if action == "ENTRY" else -expected["direction"]) > 0
            else "SELL"
        )
        action_error = None
        if complete and order_count != 1:
            action_error = f"expected one order, got {order_count}"
        elif complete and _side_name(action_orders[0]["status"]) != "FILLED":
            action_error = f"order status {_side_name(action_orders[0]['status'])}, expected FILLED"
        elif complete and len(action_fills) != 1:
            action_error = f"expected one fill, got {len(action_fills)}"
        elif len(action_fills) == 1:
            fill = action_fills[0]
            if _side_name(fill["side"]) != expected_side:
                action_error = f"wrong side {_side_name(fill['side'])}, expected {expected_side}"
            elif str(fill["instrument_id"]) != f"{event['symbol']}-LINEAR.BYBIT":
                action_error = "wrong instrument"
            elif fill["_ts_last_ns"] != expected_fill_ns:
                action_error = "wrong fill timestamp"
            elif mark is None:
                action_error = "expected fill-source mark missing"
            else:
                expected_price = float(mark["RealOpen"])
                relative_error = abs(float(fill["avg_px"]) - expected_price) / max(
                    abs(expected_price), 1e-300
                )
                if relative_error > relative_price_tolerance:
                    action_error = (
                        f"wrong fill price relative error {relative_error:.3g}"
                    )
        if action_error is not None:
            errors.append(f"{expected['event_id']} {action}: {action_error}")
        action_records.append(
            {
                "event_id": expected["event_id"],
                "symbol": event["symbol"],
                "action": action,
                "client_order_id": client_id,
                "expected_side": expected_side,
                "expected_fill_source_ts": expected_source_ts,
                "actual_fill_source_ts": (
                    expected_source_ts
                    if len(action_fills) == 1
                    and action_fills[0]["_ts_last_ns"]
                    == expected_fill_ns
                    else None
                ),
                "order_count": order_count,
                "fill_count": len(action_fills),
                "action_reconciliation_status": (
                    "RECONCILED" if complete and action_error is None else "UNAVAILABLE"
                    if not complete else "MISMATCH"
                ),
                "action_reconciliation_reason": action_error,
            }
        )

    actions = (
        pl.DataFrame(action_records, infer_schema_length=None)
        if action_records
        else pl.DataFrame(
            schema={
                "event_id": pl.String,
                "symbol": pl.String,
                "action": pl.String,
                "client_order_id": pl.String,
                "expected_side": pl.String,
                "expected_fill_source_ts": pl.Datetime("us", "UTC"),
                "actual_fill_source_ts": pl.Datetime("us", "UTC"),
                "order_count": pl.Int64,
                "fill_count": pl.Int64,
                "action_reconciliation_status": pl.String,
                "action_reconciliation_reason": pl.String,
            }
        )
    )
    summaries = []
    for event in events.iter_rows(named=True):
        rows = actions.filter(pl.col("event_id") == event["event_id"])
        complete_pair = rows.height == 2 and rows["fill_count"].to_list() == [1, 1]
        if not event["4h_available"]:
            if not event["outcome_unavailable_reason"]:
                errors.append(f"{event['event_id']}: unavailable event lacks frozen reason")
            if complete_pair:
                errors.append(
                    f"{event['event_id']}: unavailable event masquerades as complete fill pair"
                )
            status = "UNAVAILABLE"
        else:
            status = (
                "RECONCILED"
                if rows.height == 2
                and set(rows["action"].to_list()) == {"ENTRY", "EXIT"}
                and set(rows["action_reconciliation_status"].to_list()) == {"RECONCILED"}
                else "MISMATCH"
            )
        summaries.append(
            {
                "event_id": event["event_id"],
                "fill_reconciliation_status": status,
                "fill_reconciliation_reason": event["outcome_unavailable_reason"]
                if status == "UNAVAILABLE"
                else None,
            }
        )
    if errors or any(row["fill_reconciliation_status"] == "MISMATCH" for row in summaries):
        detail = "; ".join(errors[:8])
        raise RuntimeError(f"fill reconciliation failed: {detail}")
    return {
        "actions": actions.sort(["event_id", "action"]),
        "events": pl.DataFrame(summaries, infer_schema_length=None).sort("event_id"),
    }
