"""Common-origin clock and per-arm breakout episode schedules.

Design section 5: "The common origin clock is fixed before any native parameter is applied ...
every warm H1 bar satisfying the parameter-free candlestick-shape predicate is a breakout origin."
Design section 8 gives the frozen entry rule; only the threshold and pending expiry may vary, and
only through the predeclared native arms.

Index convention (design section 8, cTrader style): on a completed decision bar ``t``,
``[0] = t``, ``[1] = t - 1``, ``[2] = t - 2``.

``EXPIRED``, ``FILLED`` and ``BLOCKED_ACTIVE`` are execution states: they are resolved by the
Nautilus strategy, never here. This module emits only ``NO_EVENT`` or ``ORDER_CREATED``.
"""

from __future__ import annotations

import hashlib
import math

import polars as pl

from xen.adaptive_management.contracts import EntryOrderType, OriginState

BREAKOUT_VARIANT = "BREAKOUT"
FIXED_THRESHOLD_ATR = 0.50  # design section 8
FIXED_EXPIRY_BARS = 2  # design section 8
FIXED_ACTIVE_HOLD_BARS = 1  # design section 8: plain baseline exits after one H1 bar


def _origin_id(symbol: str, ts_ns: int, side: int, kind: str = "BREAKOUT") -> str:
    """Stable, arm-independent origin identifier."""
    digest = hashlib.sha256(f"{kind}|{symbol}|{ts_ns}|{side}".encode()).hexdigest()[:16]
    return f"{symbol}-{side:+d}-{digest}"


def _episode_identity(
    experiment_id: str,
    entry_variant: str,
    origin_id: str,
    arm_id: str,
    event_ts: object,
    event_type: str,
    side: int,
) -> tuple[str, str]:
    material = (
        f"{experiment_id}|{entry_variant}|{origin_id}|{arm_id}|"
        f"{event_ts}|{event_type}|{side:+d}"
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"{experiment_id}|{entry_variant}|{digest}", f"AM-{digest[:32]}"


def breakout_origins(h1: pl.DataFrame) -> pl.DataFrame:
    """Every warm H1 bar whose candlestick shape qualifies, before any threshold is applied.

    A bar may qualify on both the long and the short shape; each qualifying shape is its own
    origin so that every origin carries exactly one side and exactly one state per arm.

    At actionable row ``t``, reads completed bars ``t-1``, ``t-2`` and ``t-3`` plus the
    feature-panel ``atr20[t]``, which is itself frozen through ``t-1``.
    """
    required = {"symbol", "ts", "open", "high", "low", "close", "atr20"}
    missing = required - set(h1.columns)
    if missing:
        raise ValueError(f"breakout_origins requires columns {sorted(missing)}")

    base = h1.sort(["symbol", "ts"]).with_columns(
        pl.col("ts").shift(1).over("symbol").alias("signal_ts"),
        pl.col("low").shift(1).over("symbol").alias("low_0"),
        pl.col("low").shift(2).over("symbol").alias("low_1"),
        pl.col("low").shift(3).over("symbol").alias("low_2"),
        pl.col("high").shift(1).over("symbol").alias("high_0"),
        pl.col("high").shift(2).over("symbol").alias("high_1"),
        pl.col("high").shift(3).over("symbol").alias("high_2"),
        pl.col("close").shift(1).over("symbol").alias("close_0"),
        pl.col("close").shift(2).over("symbol").alias("close_1"),
    )
    long_shape = base.filter(
        pl.col("low_0").is_not_null()
        & pl.col("low_1").is_not_null()
        & pl.col("low_2").is_not_null()
        & pl.col("atr20").is_not_null()
        & (pl.col("low_1") < pl.min_horizontal("low_0", "low_2"))
    ).with_columns(pl.lit(1, dtype=pl.Int64).alias("side"))
    short_shape = base.filter(
        pl.col("high_0").is_not_null()
        & pl.col("high_1").is_not_null()
        & pl.col("high_2").is_not_null()
        & pl.col("atr20").is_not_null()
        & (pl.col("high_1") > pl.max_horizontal("high_0", "high_2"))
    ).with_columns(pl.lit(-1, dtype=pl.Int64).alias("side"))

    origins = pl.concat([long_shape, short_shape]).with_columns(
        (
            pl.col("side") * (pl.col("close_0") - pl.col("close_1")) / pl.col("atr20")
        ).alias("impulse_atr"),
        pl.when(pl.col("side") == 1)
        .then(pl.col("high_0"))
        .otherwise(pl.col("low_0"))
        .alias("stop_price_candidate"),
        pl.lit(BREAKOUT_VARIANT).alias("entry_variant"),
    )
    ts_ns = origins["ts"].cast(pl.Datetime("ns")).to_physical().to_list()
    origins = origins.with_columns(
        pl.Series(
            "origin_id",
            [
                _origin_id(sym, ts, side)
                for sym, ts, side in zip(
                    origins["symbol"].to_list(), ts_ns, origins["side"].to_list(), strict=True
                )
            ],
        )
    )
    return origins.select(
        "origin_id",
        "symbol",
        pl.col("ts").alias("decision_ts"),
        "signal_ts",
        "entry_variant",
        "side",
        "atr20",
        "impulse_atr",
        "stop_price_candidate",
    ).sort(["symbol", "decision_ts", "side"])


def breakout_episodes(
    origins: pl.DataFrame,
    threshold_atr: float | pl.Expr,
    expiry_bars: int | pl.Expr,
    *,
    experiment_id: str = "SPDR-021",
    native_arm_id: str = "FIXED_NATIVE_BREAKOUT",
) -> pl.DataFrame:
    """One row per origin for one arm: order created at the frozen stop, or no event.

    ``threshold_atr`` and ``expiry_bars`` may be per-origin expressions (adaptive arms) or
    scalars (fixed comparator). The breakout rule is a strict ``>`` comparison, so an impulse
    exactly equal to the threshold creates no order.
    """
    threshold = (
        threshold_atr if isinstance(threshold_atr, pl.Expr) else pl.lit(float(threshold_atr))
    )
    expiry = expiry_bars if isinstance(expiry_bars, pl.Expr) else pl.lit(int(expiry_bars))
    created = pl.col("impulse_atr") > pl.col("threshold_atr")
    episodes = origins.with_columns(
        threshold.alias("threshold_atr"),
        expiry.cast(pl.Int64).alias("expiry_bars"),
    ).with_columns(
        pl.when(created)
        .then(pl.lit(str(OriginState.ORDER_CREATED)))
        .otherwise(pl.lit(str(OriginState.NO_EVENT)))
        .alias("state"),
        pl.when(created).then(pl.col("stop_price_candidate")).otherwise(None).alias("stop_price"),
    )
    identities = [
        _episode_identity(
            experiment_id,
            BREAKOUT_VARIANT,
            row["origin_id"],
            native_arm_id,
            row["signal_ts"],
            "STOP_ORDER" if row["state"] == str(OriginState.ORDER_CREATED) else "NO_EVENT",
            row["side"],
        )
        for row in episodes.iter_rows(named=True)
    ]
    return episodes.with_columns(
        pl.Series("episode_id", [item[0] for item in identities]),
        pl.Series("position_id", [item[1] for item in identities]),
        pl.when(created).then(pl.col("signal_ts")).otherwise(None).alias("event_ts"),
        pl.lit(None, dtype=pl.Datetime("us", "UTC")).alias("entry_ts"),
        pl.col("decision_ts").alias("actionable_ts"),
        pl.when(created)
        .then(pl.lit(str(EntryOrderType.STOP)))
        .otherwise(pl.lit(str(EntryOrderType.NONE)))
        .alias("entry_order_type"),
        pl.lit(experiment_id).alias("experiment_id"),
        pl.lit(native_arm_id).alias("native_arm_id"),
    ).select(
        "episode_id",
        "position_id",
        "origin_id",
        "experiment_id",
        "native_arm_id",
        "symbol",
        "decision_ts",
        "event_ts",
        "entry_ts",
        "actionable_ts",
        "entry_order_type",
        "entry_variant",
        "side",
        "atr20",
        "impulse_atr",
        "threshold_atr",
        "expiry_bars",
        "stop_price",
        "state",
    )


def breach_origins(h1: pl.DataFrame, features: pl.DataFrame) -> pl.DataFrame:
    """Every H1 zone origin, with a bounded future path retained for arm materialisation."""
    required = {"symbol", "ts", "open", "high", "low", "close"}
    missing = required - set(h1.columns)
    if missing:
        raise ValueError(f"breach_origins requires columns {sorted(missing)}")
    joined = h1.sort(["symbol", "ts"]).join(
        features.select("symbol", "ts", "range_scale_bps"),
        on=["symbol", "ts"],
        how="left",
    )
    rows: list[dict] = []
    for symbol, group in joined.group_by("symbol", maintain_order=True):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        records = group.sort("ts").to_dicts()
        for index, row in enumerate(records[:-1]):
            ts_ns = int(pl.Series([row["ts"]]).cast(pl.Datetime("ns")).to_physical()[0])
            # The decision uses t-1 features at the open of this row; this row is the
            # SPDR-014 anchor and the first causally observed event bar.
            path = records[index : index + 25]
            rows.append(
                {
                    "origin_id": _origin_id(name, ts_ns, 0, "BREACH"),
                    "symbol": name,
                    "decision_ts": row["ts"],
                    "anchor_price": row["open"],
                    "range_scale_bps": row.get("range_scale_bps"),
                    "component_ready": (
                        row.get("range_scale_bps") is not None
                        and math.isfinite(float(row["range_scale_bps"]))
                    ),
                    "_path_ts": [item["ts"] for item in path],
                    "_path_open": [item["open"] for item in path],
                    "_path_high": [item["high"] for item in path],
                    "_path_low": [item["low"] for item in path],
                    "_path_close": [item["close"] for item in path],
                }
            )
    return pl.DataFrame(rows)


def breach_episodes(
    origins: pl.DataFrame,
    experiment_id: str,
    event: str,
    *,
    z: float | pl.Series,
    horizon: int | pl.Series,
    native_arm_id: str,
) -> pl.DataFrame:
    """SPDR-014-parity first-touch/first-close events with next-real-open entry."""
    if experiment_id not in {"SPDR-022", "SPDR-023"}:
        raise ValueError("breach episodes require SPDR-022 or SPDR-023")
    if event not in {"E_TOUCH", "E_CLOSE"}:
        raise ValueError("event must be E_TOUCH or E_CLOSE")
    z_values = z.to_list() if isinstance(z, pl.Series) else [float(z)] * origins.height
    h_values = horizon.to_list() if isinstance(horizon, pl.Series) else [int(horizon)] * origins.height
    out: list[dict] = []
    for row, z_value, h_value in zip(
        origins.iter_rows(named=True), z_values, h_values, strict=True
    ):
        record = {key: value for key, value in row.items() if not key.startswith("_path_")}
        variant = event
        breach_side = 0
        event_index: int | None = None
        entry_index: int | None = None
        state = str(OriginState.NO_EVENT)
        path_size = len(row["_path_ts"])
        ready = (
            row["component_ready"]
            and z_value is not None
            and math.isfinite(float(z_value))
            and h_value is not None
            and int(h_value) > 0
        )
        if not ready:
            state = str(OriginState.NO_FEATURE)
        elif path_size < int(h_value):
            state = str(OriginState.INCOMPLETE)
        else:
            half = float(z_value) * float(row["range_scale_bps"]) / 1e4
            upper = float(row["anchor_price"]) * (1.0 + half)
            lower = float(row["anchor_price"]) * (1.0 - half)
            for index in range(int(h_value)):
                if event == "E_TOUCH":
                    up = row["_path_high"][index] >= upper
                    down = row["_path_low"][index] <= lower
                    if up or down:
                        if up and down:
                            centre = float(row["anchor_price"])
                            up_ext = (row["_path_high"][index] - centre) / centre * 1e4
                            down_ext = (centre - row["_path_low"][index]) / centre * 1e4
                            breach_side = 0 if abs(up_ext - down_ext) < 1e-9 else (
                                1 if up_ext > down_ext else -1
                            )
                        else:
                            breach_side = 1 if up else -1
                        event_index = index
                        break
                else:
                    close = row["_path_close"][index]
                    if close > upper or close < lower:
                        breach_side = 1 if close > upper else -1
                        event_index = index
                        break
            if event_index is not None:
                if breach_side == 0:
                    state = str(OriginState.EVENT_UNDECIDED)
                else:
                    entry_index = event_index + 1
                    state = (
                        str(OriginState.ORDER_CREATED)
                        if entry_index < path_size
                        else str(OriginState.CENSORED)
                    )
        trade_side = breach_side if experiment_id == "SPDR-022" else -breach_side
        event_ts = row["_path_ts"][event_index] if event_index is not None else None
        entry_ts = (
            row["_path_ts"][entry_index]
            if state == str(OriginState.ORDER_CREATED) and entry_index is not None
            else None
        )
        if state == str(OriginState.ORDER_CREATED):
            actionable_ts = entry_ts
            entry_order_type = str(EntryOrderType.MARKET)
        elif state in {
            str(OriginState.EVENT_UNDECIDED),
            str(OriginState.CENSORED),
        }:
            actionable_ts = event_ts
            entry_order_type = str(EntryOrderType.NONE)
        elif state == str(OriginState.NO_EVENT):
            actionable_ts = row["_path_ts"][int(h_value) - 1]
            entry_order_type = str(EntryOrderType.NONE)
        elif state == str(OriginState.INCOMPLETE):
            actionable_ts = row["_path_ts"][-1]
            entry_order_type = str(EntryOrderType.NONE)
        else:
            actionable_ts = row["decision_ts"]
            entry_order_type = str(EntryOrderType.NONE)
        episode_id, position_id = _episode_identity(
            experiment_id, variant, row["origin_id"], native_arm_id,
            event_ts or actionable_ts, f"{event}:{state}", trade_side,
        )
        record.update(
            {
                "episode_id": episode_id,
                "position_id": position_id,
                "experiment_id": experiment_id,
                "native_arm_id": native_arm_id,
                "entry_variant": variant,
                "event_type": event,
                "event_ts": event_ts,
                "entry_ts": entry_ts,
                "actionable_ts": actionable_ts,
                "entry_order_type": entry_order_type,
                "side": trade_side,
                "z": z_value,
                "horizon": h_value,
                "stop_price": None,
                "expiry_bars": None,
                "state": state,
            }
        )
        out.append(record)
    return pl.from_dicts(out, infer_schema_length=None).with_columns(
        pl.col(column).cast(pl.Datetime("ns", "UTC"))
        for column in ("decision_ts", "event_ts", "entry_ts", "actionable_ts")
    )
